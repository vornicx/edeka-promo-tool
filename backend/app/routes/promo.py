import base64
import base64
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uuid

from app.schemas.promotion import (
    PromotionSpec,
    EnrichmentSpec,
    CreativeDirection,
    FormatType,
    EXPORT_FORMATS,
)
from app.services.intake import validate_and_create_spec
from app.services.planner import build_local_plan, generate_ai_plan
from app.services.composer import compose_promotion
from app.services.exporter import export_promotion
from app.adapters import (
    OpenAICompatibleAdapter,
    GeminiAdapter,
    OllamaAdapter,
    FallbackChainAdapter,
    FallbackChainExhausted,
)
from app.user_settings import load_user_settings
from app.config import settings

router = APIRouter(prefix="/api/promo", tags=["promo"])

MAX_SESSIONS = 50
sessions: dict[str, dict] = {}


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


def _build_fallback_chain() -> FallbackChainAdapter:
    user_settings = load_user_settings()
    enabled = user_settings.get_enabled_providers()

    adapters = []
    for cfg in enabled:
        try:
            if cfg.type == "gemini":
                adapters.append(GeminiAdapter(api_key=cfg.api_key, model=cfg.model, base_url=cfg.base_url))
            elif cfg.type == "ollama":
                adapters.append(OllamaAdapter(model=cfg.model, base_url=cfg.base_url))
            else:
                # openrouter, github, nvidia, custom → all OpenAI-compatible
                adapters.append(OpenAICompatibleAdapter(api_key=cfg.api_key, base_url=cfg.base_url, model=cfg.model))
        except ValueError as e:
            import logging
            logging.getLogger(__name__).warning("Anbieter %s (%s) uebersprungen: %s", cfg.type, cfg.model, e)

    if not adapters:
        raise ValueError("Keine KI-Anbieter konfiguriert")

    return FallbackChainAdapter(adapters)


class CreatePromoRequest(BaseModel):
    product: str
    category: Optional[str] = None
    price: str
    old_price: Optional[str] = None
    validity: str
    origin: Optional[str] = None
    claim: Optional[str] = None
    product_image: Optional[str] = None
    format: str = "post"
    style: str = "edeka"
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
        raise HTTPException(status_code=400, detail=f"Eingabedaten konnten nicht verarbeitet werden: {e}")

    session_id = str(uuid.uuid4())[:8]
    _cleanup_old_sessions()

    # Resolve product image for vision-enhanced planning
    image_base64 = _resolve_product_image_base64(request.product_image)

    try:
        chain = _build_fallback_chain()
    except ValueError as e:
        enrichment, directions = build_local_plan(spec)
        generation_mode = "local"
        generation_note = str(e)
    else:
        try:
            enrichment, directions = await generate_ai_plan(chain, spec, image_base64)
            generation_mode = "ai"
            generation_note = f"KI-Planung erfolgreich über {chain.__class__.__name__}"
        except FallbackChainExhausted as e:
            enrichment, directions = build_local_plan(spec)
            generation_mode = "local_fallback"
            generation_note = f"Alle KI-Anbieter waren nicht verfügbar. Lokaler Profi-Modus wurde verwendet. Fehler: {e}"
        except Exception as e:
            enrichment, directions = build_local_plan(spec)
            generation_mode = "local_fallback"
            generation_note = f"KI-Fehler: {e}"

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
