import base64
import io
import logging
import re
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
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
from app.services.image_generator import generate_event_background
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


class PromoItemIn(BaseModel):
    name: str = ""
    price: str = ""
    old_price: Optional[str] = None
    category: Optional[str] = None
    product_image: Optional[str] = None


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
    accent_color: Optional[str] = None
    price_size: str = "auto"
    items: list[PromoItemIn] = []
    use_ai_planning: bool = False


class SelectDirectionRequest(BaseModel):
    session_id: str
    direction_index: int


class SessionRequest(BaseModel):
    session_id: str


class SelectVariantRequest(BaseModel):
    session_id: str
    index: int


class ExportRequest(BaseModel):
    session_id: str
    format: str


STYLE_LABELS = {
    "edeka": "EDEKA Style",
    "luxe": "Dark Luxe",
    "editorial": "Editorial",
    "colorblock": "Color Block",
    "frischemarkt": "Frischemarkt",
    "prospekt": "Prospekt",
    "markttafel": "Markt-Tafel",
    "bio": "Bio / Natur",
}

# Complementary looks offered as one-click alternatives next to the chosen style.
ALT_STYLES = {
    "edeka": ["prospekt", "frischemarkt"],
    "luxe": ["markttafel", "editorial"],
    "editorial": ["frischemarkt", "luxe"],
    "colorblock": ["edeka", "prospekt"],
    "frischemarkt": ["bio", "edeka"],
    "prospekt": ["edeka", "colorblock"],
    "markttafel": ["luxe", "bio"],
    "bio": ["frischemarkt", "markttafel"],
}


def _variant_defs(spec, directions) -> list[dict]:
    """Which design variants to offer for one briefing.

    - KI-Stil: die drei Kreativrichtungen der Planung.
    - Vorlagen-Stil: der gewählte Look plus zwei passende Alternativen.
    - Wochenangebote: ein festes Prospekt-Layout, keine Varianten.
    """
    style = (spec.style or "edeka").lower()
    if spec.campaign_kind.value == "multi":
        return [{"label": "Wochenangebote", "style": style, "direction_index": 0}]
    if style == "ai":
        return [
            {"label": d.name, "style": "ai", "direction_index": i}
            for i, d in enumerate(directions[:3])
        ]
    variants = [{"label": STYLE_LABELS.get(style, style.title()), "style": style, "direction_index": 0}]
    for alt in ALT_STYLES.get(style, ["edeka", "prospekt"]):
        variants.append({"label": STYLE_LABELS.get(alt, alt.title()), "style": alt, "direction_index": 0})
    return variants


def _compose_variant(session, session_id: str, variant: dict, fmt: FormatType, output_path: Path) -> Path:
    """Compose one variant of the session's briefing at the given format."""
    spec = session["spec"]
    vspec = spec.model_copy(update={"style": variant["style"], "format": fmt})
    index = min(variant.get("direction_index", 0), len(session["directions"]) - 1)
    direction = session["directions"][index]
    compose_promotion(
        vspec, direction, fmt, output_path,
        event_background=session.get("event_background"),
    )
    return output_path


def _selected_variant(session) -> dict:
    variants = session.get("variants") or []
    sel = session.get("selected_variant", 0)
    if variants and 0 <= sel < len(variants):
        return variants[sel]
    spec = session["spec"]
    return {"label": "", "style": spec.style, "direction_index": 0}


def _export_slug(value: str) -> str:
    clean = re.sub(r"[^\w]+", "_", value.lower()).strip("_")
    return clean or "promotion"


@router.post("/create")
async def create_promo(request: CreatePromoRequest):
    try:
        spec = validate_and_create_spec(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Eingabedaten konnten nicht verarbeitet werden: {e}")

    session_id = str(uuid.uuid4())[:8]
    _cleanup_old_sessions()

    # Product photos are only context for product offers. Event posters must be
    # generated from event components, not from stored product assets.
    image_base64 = None if spec.campaign_kind.value == "event" else _resolve_product_image_base64(request.product_image)

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


async def _ensure_event_background(session, spec, fmt: FormatType, output_dir: Path):
    """Generate (once per session) the AI event background and cache it."""
    if spec.campaign_kind.value != "event" or (spec.style or "").lower() != "ai":
        return None
    if session.get("event_background"):
        return session["event_background"]
    direction = session["directions"][0]
    background = await generate_event_background(spec, direction, fmt, output_dir)
    if background is None:
        raise HTTPException(
            status_code=502,
            detail=(
                "Das KI-Bild konnte nicht erstellt werden. Bitte OpenRouter API-Key und Bildmodell "
                "prüfen. Im KI-Eventmodus wird kein einfaches Komponenten-Layout als Ersatz erzeugt."
            ),
        )
    session["event_background"] = background
    return background


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
    await _ensure_event_background(session, spec, fmt, output_dir)

    try:
        compose_promotion(spec, direction, fmt, output_path, event_background=session.get("event_background"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gestaltung konnte nicht erstellt werden: {e}")

    session["composed_path"] = output_path
    session["variants"] = [
        {"label": direction.name, "style": spec.style, "direction_index": request.direction_index, "path": output_path}
    ]
    session["selected_variant"] = 0

    return {
        "session_id": request.session_id,
        "image_url": f"/api/promo/image/{request.session_id}",
        "direction": direction.name,
    }


@router.post("/compose_all")
async def compose_all(request: SessionRequest):
    """Compose every design variant for the briefing so the user can pick one
    visually: 3 Kreativrichtungen im KI-Stil bzw. gewählter Look + 2 Alternativen."""
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")

    spec = session["spec"]
    fmt = FormatType(spec.format.value)
    output_dir = settings.output_dir / request.session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    await _ensure_event_background(session, spec, fmt, output_dir)

    defs = _variant_defs(spec, session["directions"])
    composed: list[dict] = []
    errors: list[str] = []
    for i, variant in enumerate(defs):
        path = output_dir / f"variant_{i}.png"
        try:
            _compose_variant(session, request.session_id, variant, fmt, path)
        except Exception as e:  # noqa: BLE001 - a broken alternative must not kill the main design
            logger.warning("Variante %s fehlgeschlagen: %s", variant.get("label"), e)
            errors.append(f"{variant.get('label')}: {e}")
            continue
        composed.append({**variant, "path": path})

    if not composed:
        raise HTTPException(status_code=500, detail=f"Gestaltung konnte nicht erstellt werden: {'; '.join(errors)}")

    session["variants"] = composed
    session["selected_variant"] = 0
    session["composed_path"] = composed[0]["path"]

    return {
        "session_id": request.session_id,
        "selected": 0,
        "variants": [
            {
                "index": i,
                "label": v["label"],
                "image_url": f"/api/promo/image/{request.session_id}/variant/{i}",
            }
            for i, v in enumerate(composed)
        ],
    }


@router.post("/select_variant")
async def select_variant(request: SelectVariantRequest):
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sitzung nicht gefunden")
    variants = session.get("variants") or []
    if request.index < 0 or request.index >= len(variants):
        raise HTTPException(status_code=400, detail="Ungueltige Variante")
    session["selected_variant"] = request.index
    session["composed_path"] = variants[request.index]["path"]
    return {"session_id": request.session_id, "selected": request.index}


@router.get("/image/{session_id}")
async def get_image(session_id: str):
    session = sessions.get(session_id)
    if not session or not session["composed_path"]:
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")

    path = session["composed_path"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Bilddatei nicht gefunden")

    return FileResponse(str(path), media_type="image/png")


@router.get("/image/{session_id}/variant/{index}")
async def get_variant_image(session_id: str, index: int):
    session = sessions.get(session_id)
    variants = (session or {}).get("variants") or []
    if not session or index < 0 or index >= len(variants):
        raise HTTPException(status_code=404, detail="Variante nicht gefunden")
    path = variants[index]["path"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Bilddatei nicht gefunden")
    return FileResponse(str(path), media_type="image/png")


def _export_native(session, session_id: str, fmt: FormatType) -> Path:
    """Export by re-composing the selected variant at the target format's native
    size — true per-format layout instead of stretching the preview image."""
    variant = _selected_variant(session)
    out = settings.output_dir / session_id / f"export_{fmt.value}.png"
    try:
        return _compose_variant(session, session_id, variant, fmt, out)
    except Exception:  # noqa: BLE001 - fall back to the plain resize export
        return export_promotion(session["composed_path"], fmt, settings.output_dir / session_id)


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
        exported_path = _export_native(session, request.session_id, fmt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export konnte nicht erstellt werden: {e}")

    return FileResponse(
        str(exported_path),
        media_type="image/png",
        filename=f"edeka_{_export_slug(session['spec'].product)}_{fmt.value}.png",
    )


@router.post("/export_zip")
async def export_zip(request: SessionRequest):
    """All four formats of the selected design in one ZIP download."""
    session = sessions.get(request.session_id)
    if not session or not session["composed_path"]:
        raise HTTPException(status_code=404, detail="Promotion wurde noch nicht gestaltet")

    slug = _export_slug(session["spec"].product)
    buf = io.BytesIO()
    try:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fmt in FormatType:
                path = _export_native(session, request.session_id, fmt)
                zf.write(path, arcname=f"edeka_{slug}_{fmt.value}.png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZIP-Export konnte nicht erstellt werden: {e}")

    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="edeka_{slug}_alle_formate.zip"'},
    )


@router.post("/export_pdf")
async def export_pdf(request: ExportRequest):
    """Print-ready PDF (300 dpi) — A4/A5 land exactly on the paper size."""
    session = sessions.get(request.session_id)
    if not session or not session["composed_path"]:
        raise HTTPException(status_code=404, detail="Promotion wurde noch nicht gestaltet")

    try:
        fmt = FormatType(request.format)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungueltiges Format")

    try:
        png_path = _export_native(session, request.session_id, fmt)
        from PIL import Image

        pdf_path = png_path.with_suffix(".pdf")
        with Image.open(png_path) as img:
            img.convert("RGB").save(str(pdf_path), "PDF", resolution=300.0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF-Export konnte nicht erstellt werden: {e}")

    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=f"edeka_{_export_slug(session['spec'].product)}_{fmt.value}.pdf",
    )


@router.get("/templates")
async def list_templates():
    return {
        "templates": [
            {"key": k, "label": v.label, "width": v.width, "height": v.height}
            for k, v in EXPORT_FORMATS.items()
        ]
    }
