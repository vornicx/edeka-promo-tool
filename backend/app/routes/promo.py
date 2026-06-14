from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid

from app.schemas.promotion import (
    PromotionSpec,
    EnrichmentSpec,
    CreativeDirection,
    FormatType,
    EXPORT_FORMATS,
)
from app.services.intake import validate_and_create_spec
from app.services.enricher import enrich_promotion
from app.services.director import generate_directions
from app.services.composer import compose_promotion
from app.services.exporter import export_promotion
from app.adapters.openrouter_adapter import OpenRouterAdapter
from app.config import settings

router = APIRouter(prefix="/api/promo", tags=["promo"])

ai_adapter = OpenRouterAdapter()

MAX_SESSIONS = 50
sessions: dict[str, dict] = {}


def _cleanup_old_sessions():
    if len(sessions) >= MAX_SESSIONS:
        oldest_keys = list(sessions.keys())[: len(sessions) // 2]
        for key in oldest_keys:
            del sessions[key]


class CreatePromoRequest(BaseModel):
    product: str
    category: Optional[str] = None
    price: str
    old_price: Optional[str] = None
    validity: str
    origin: Optional[str] = None
    claim: Optional[str] = None
    format: str = "post"
    tone: str = "fresco"
    differentiation_level: str = "medio"


class SelectDirectionRequest(BaseModel):
    session_id: str
    direction_index: int


class ExportRequest(BaseModel):
    session_id: str
    format: str


@router.post("/create")
async def create_promo(request: CreatePromoRequest):
    try:
        spec = validate_and_create_spec(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en datos de entrada: {e}")

    session_id = str(uuid.uuid4())[:8]

    _cleanup_old_sessions()

    try:
        enrichment = await enrich_promotion(ai_adapter, spec)
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Error en enriquecimiento IA: {e}"
        )

    try:
        directions = await generate_directions(ai_adapter, spec, enrichment)
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Error en dirección creativa IA: {e}"
        )

    sessions[session_id] = {
        "spec": spec,
        "enrichment": enrichment,
        "directions": directions,
        "composed_path": None,
    }

    return {
        "session_id": session_id,
        "spec": spec.model_dump(),
        "enrichment": enrichment.model_dump(),
        "directions": [d.model_dump() for d in directions],
    }


@router.post("/compose")
async def compose_selected(request: SelectDirectionRequest):
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if request.direction_index < 0 or request.direction_index >= len(
        session["directions"]
    ):
        raise HTTPException(status_code=400, detail="Índice de dirección inválido")

    spec = session["spec"]
    direction = session["directions"][request.direction_index]
    fmt = FormatType(spec.format.value)

    output_dir = settings.output_dir / request.session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"promo_{direction.name}.png"

    try:
        compose_promotion(spec, direction, fmt, output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en composición: {e}")

    session["composed_path"] = output_path

    return {
        "session_id": request.session_id,
        "image_url": f"/api/promo/image/{request.session_id}",
        "direction": direction.name,
    }


@router.get("/image/{session_id}")
async def get_image(session_id: str):
    session = sessions.get(session_id)
    if not session or not session["composed_path"]:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    path = session["composed_path"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo de imagen no encontrado")

    return FileResponse(str(path), media_type="image/png")


@router.post("/export")
async def export_to_format(request: ExportRequest):
    session = sessions.get(request.session_id)
    if not session or not session["composed_path"]:
        raise HTTPException(status_code=404, detail="Promoción no compuesta aún")

    try:
        fmt = FormatType(request.format)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato inválido")

    try:
        exported_path = export_promotion(
            session["composed_path"], fmt, settings.output_dir / request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en exportación: {e}")

    return FileResponse(
        str(exported_path),
        media_type="image/png",
        filename=f"edeka_promo_{session['spec'].product}_{fmt.value}.png",
    )


@router.get("/templates")
async def list_templates():
    return {
        "templates": [
            {"key": k, "label": v.label, "width": v.width, "height": v.height}
            for k, v in EXPORT_FORMATS.items()
        ]
    }
