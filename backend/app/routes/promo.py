import base64
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uuid

from app.schemas.promotion import (
    EXPORT_FORMATS,
    FormatType,
    PromotionSpec,
)
from app.services.intake import validate_and_create_spec
from app.services.planner import build_local_plan, generate_ai_plan
from app.services.composer import compose_promotion
from app.services.exporter import export_promotion
from app.adapters import OpenAICompatibleAdapter
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/promo", tags=["promo"])

MAX_SESSIONS = 50
sessions: dict[str, dict] = {}
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def _cleanup_old_sessions():
    if len(sessions) >= MAX_SESSIONS:
        oldest_keys = list(sessions.keys())[: len(sessions) // 2]
        for key in oldest_keys:
            del sessions[key]


def _resolve_product_image_base64(product_image: str | None) -> str | None:
    """Resolve a product_image key (builtin:X or custom:Y) to a base64 data-URI."""
    if not product_image or not product_image.strip():
        return None

    path: Path | None = None
    choice = product_image.strip()

    if choice.startswith("builtin:"):
        from app.builtin_products import builtin_file
        path = builtin_file(choice.split(":", 1)[1])
    elif choice.startswith("custom:"):
        from app.product_library import get_product_file
        path = get_product_file(choice.split(":", 1)[1])

    if not path or not path.exists():
        return None

    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    # Determine mime type from extension
    ext = path.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


def _build_ai_adapter() -> OpenAICompatibleAdapter | None:
    """Create an OpenRouter adapter from user settings. Returns None if no API key."""
    from app.user_settings import get_effective_ai_settings
    ai = get_effective_ai_settings()
    if not ai.api_key or not ai.enabled:
        return None
    try:
        return OpenAICompatibleAdapter(
            api_key=ai.api_key,
            base_url=OPENROUTER_BASE,
            model=ai.selected_model,
        )
    except ValueError:
        return None


class CreatePromoRequest(BaseModel):
    campaign_kind: str = "product"
    product: str
    category: Optional[str] = None
    price: str = ""
    old_price: Optional[str] = None
    validity: str = ""
    origin: Optional[str] = None
    claim: Optional[str] = None
    event_description: Optional[str] = None
    product_image: Optional[str] = None
    format: str = "post"
    style: str = "edeka"
    tone: str = "fresco"
    differentiation_level: str = "medio"
    use_ai_planning: bool = False


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
        raise HTTPException(status_code=400, detail=f"Eingabedaten konnten nicht verarbeitet werden: {e}")

    session_id = str(uuid.uuid4())[:8]
    _cleanup_old_sessions()

    # Resolve product image for vision-enhanced planning
    image_base64 = _resolve_product_image_base64(request.product_image)

    if not request.use_ai_planning:
        enrichment, directions = build_local_plan(spec)
        generation_mode = "local"
        generation_note = "Vorlagen-Modus gewählt"
    else:
        adapter = _build_ai_adapter()
        if adapter is None:
            enrichment, directions = build_local_plan(spec)
            generation_mode = "local"
            generation_note = "Kein OpenRouter API-Key konfiguriert. Lokaler Profi-Modus verwendet."
        else:
            try:
                enrichment, directions = await generate_ai_plan(adapter, spec, image_base64)
                generation_mode = "ai"
                generation_note = f"KI-Planung erfolgreich mit {adapter.model}"
            except Exception as e:
                logger.warning("KI-Planung fehlgeschlagen: %s", e)
                enrichment, directions = build_local_plan(spec)
                generation_mode = "local_fallback"
                generation_note = f"KI-Anbieter nicht verfügbar. Lokaler Profi-Modus verwendet. Fehler: {e}"

    sessions[session_id] = {
        "spec": spec,
        "enrichment": enrichment,
        "directions": directions,
        "composed_path": None,
        "generation_mode": generation_mode,
    }

    return {
        "session_id": session_id,
        "spec": spec.model_dump(),
        "enrichment": enrichment.model_dump(),
        "directions": [d.model_dump() for d in directions],
        "generation_mode": generation_mode,
        "generation_note": generation_note,
    }


@router.post("/compose")
async def compose_selected(request: SelectDirectionRequest):
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")

    if request.direction_index < 0 or request.direction_index >= len(
        session["directions"]
    ):
        raise HTTPException(status_code=400, detail="Ungueltige Kreativrichtung")

    spec = session["spec"]
    direction = session["directions"][request.direction_index]
    fmt = FormatType(spec.format.value)

    output_dir = settings.output_dir / request.session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"promo_{direction.name}.png"

    try:
        compose_promotion(spec, direction, fmt, output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gestaltung konnte nicht erstellt werden: {e}")

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
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")

    path = session["composed_path"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Bilddatei nicht gefunden")

    return FileResponse(str(path), media_type="image/png")


@router.post("/export")
async def export_to_format(request: ExportRequest):
    session = sessions.get(request.session_id)
    if not session or not session["composed_path"]:
        raise HTTPException(status_code=404, detail="Promotion wurde noch nicht gestaltet")

    try:
        fmt = FormatType(request.format)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungueltiges Format")

    try:
        exported_path = export_promotion(
            session["composed_path"], fmt, settings.output_dir / request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export konnte nicht erstellt werden: {e}")

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
