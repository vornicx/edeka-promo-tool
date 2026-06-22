"""On-demand example previews so the user can pick options visually.

The preview mirrors the user's real briefing (product, price, claim, motif…)
so the thumbnails look like the promotion they are actually building.
"""
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Response
from PIL import Image

from app.schemas.promotion import (
    CreativeDirection,
    DifferentiationLevel,
    FormatType,
    PromotionSpec,
    ToneType,
)
from app.services.composer import compose_promotion
from app.services.intake import normalize_price

router = APIRouter(prefix="/api/examples", tags=["examples"])

_TONES = {t.value for t in ToneType}
_LEVELS = {d.value for d in DifferentiationLevel}
_STYLES = {"edeka", "kreativ"}
_FORMATS = {f.value for f in FormatType}

_THUMB_MAX = 640  # downscale previews; full quality is for the real export
_cache: dict[str, bytes] = {}


def _render(spec: PromotionSpec, fmt: FormatType, style: str) -> bytes:
    palette = ["#004C96", "#FFD600"] if style == "edeka" else ["#1565C0", "#FFA000"]
    direction = CreativeDirection(
        name="beispiel", intent="", composition="", palette=palette,
        text_safe_area="bottom", boldness="high", waschbaer_presence="featured",
    )
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        compose_promotion(spec, direction, fmt, Path(tmp))
        img = Image.open(tmp).convert("RGB")
        if max(img.size) > _THUMB_MAX:
            img.thumbnail((_THUMB_MAX, _THUMB_MAX), Image.Resampling.LANCZOS)
        out = tmp + ".thumb.png"
        img.save(out, optimize=True)
        data = Path(out).read_bytes()
        os.unlink(out)
        return data
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


@router.get("")
async def example(
    style: str = "edeka",
    tone: str = "fresco",
    level: str = "medio",
    format: str = "post",
    product: str = "",
    price: str = "",
    old_price: str = "",
    validity: str = "",
    claim: str = "",
    origin: str = "",
    category: str = "",
    product_image: str = "",
):
    style = style.lower() if style.lower() in _STYLES else "edeka"
    tone = tone.lower() if tone.lower() in _TONES else "fresco"
    level = level.lower() if level.lower() in _LEVELS else "medio"
    fmt = FormatType(format) if format in _FORMATS else FormatType.POST

    # Fall back to a representative sample when the briefing is still empty.
    if not product.strip():
        product = "Erdbeeren"
        category = category or "Obst"
        product_image = product_image or "builtin:strawberries"
        price = price or "2,99 €"
        old_price = old_price or "3,49 €"
        validity = validity or "KW 24"
        claim = claim or "saftig & fruchtig"
        origin = origin or "aus der Region"

    spec = PromotionSpec(
        product=product.strip(),
        category=category.strip() or None,
        price=normalize_price(price) if price.strip() else "—",
        old_price=normalize_price(old_price) if old_price.strip() else None,
        validity=validity.strip() or "Angebot",
        origin=origin.strip() or None,
        claim=claim.strip() or None,
        product_image=product_image.strip() or None,
        style=style,
        tone=tone,
        differentiation_level=level,
        format=fmt,
    )

    key = "|".join([
        style, tone, level, fmt.value, spec.product, spec.price, spec.old_price or "",
        spec.validity, spec.claim or "", spec.origin or "", spec.category or "",
        spec.product_image or "",
    ])
    if key not in _cache:
        if len(_cache) > 240:
            _cache.clear()
        _cache[key] = _render(spec, fmt, style)
    return Response(content=_cache[key], media_type="image/png")
