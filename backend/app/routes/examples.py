"""On-demand example previews so the user can pick options visually.

The preview mirrors the user's real briefing (product, price, claim, motif…)
so the thumbnails look like the promotion they are actually building.
"""
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Response

from app.schemas.promotion import (
    CreativeDirection,
    DifferentiationLevel,
    EXPORT_FORMATS,
    FormatType,
    PriceSize,
    PromotionSpec,
    ToneType,
)
from app.services.composer import compose_promotion
from app.services.intake import normalize_price

router = APIRouter(prefix="/api/examples", tags=["examples"])

_TONES = {t.value for t in ToneType}
_LEVELS = {d.value for d in DifferentiationLevel}
_STYLES = {"edeka", "luxe", "editorial", "colorblock", "frischemarkt", "prospekt", "markttafel", "bio"}
_FORMATS = {f.value for f in FormatType}
_PRICE_SIZES = {p.value for p in PriceSize}

_THUMB_LONG = 380  # render previews small (and fast); export keeps full quality
_cache: dict[str, bytes] = {}


def _render(spec: PromotionSpec, fmt: FormatType) -> bytes:
    direction = CreativeDirection(
        name="beispiel", intent="", composition="",
        palette=["#004C96", "#FFD600", "#E8612C", "#FFF8F0"],
        text_safe_area="bottom", boldness="high", waschbaer_presence="featured",
    )
    f = EXPORT_FORMATS[fmt]
    scale = min(1.0, _THUMB_LONG / max(f.width, f.height))
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        compose_promotion(spec, direction, fmt, Path(tmp), scale=scale)
        return Path(tmp).read_bytes()
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


@router.get("")
async def example(
    campaign_kind: str = "product",
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
    accent_color: str = "",
    price_size: str = "auto",
):
    style = style.lower() if style.lower() in _STYLES else "edeka"
    tone = tone.lower() if tone.lower() in _TONES else "fresco"
    level = level.lower() if level.lower() in _LEVELS else "medio"
    fmt = FormatType(format) if format in _FORMATS else FormatType.POST
    campaign_kind = "event" if campaign_kind == "event" else "product"
    price_size = price_size.lower() if price_size.lower() in _PRICE_SIZES else "auto"

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
        campaign_kind=campaign_kind,
        product=product.strip(),
        category=category.strip() or None,
        price=(price.strip() if campaign_kind == "event" else normalize_price(price)) if price.strip() else ("EVENT" if campaign_kind == "event" else "—"),
        old_price=None if campaign_kind == "event" else (normalize_price(old_price) if old_price.strip() else None),
        validity=validity.strip() or "nur heute",
        origin=origin.strip() or None,
        claim=claim.strip() or None,
        product_image=product_image.strip() or None,
        style=style,
        tone=tone,
        differentiation_level=level,
        format=fmt,
        accent_color=accent_color.strip() or None,
        price_size=price_size,
    )

    key = "|".join([
        campaign_kind, style, tone, level, fmt.value, spec.product, spec.price, spec.old_price or "",
        spec.validity, spec.claim or "", spec.origin or "", spec.category or "",
        spec.product_image or "", accent_color.strip(), price_size,
    ])
    if key not in _cache:
        if len(_cache) > 240:
            _cache.clear()
        _cache[key] = _render(spec, fmt)
    return Response(
        content=_cache[key],
        media_type="image/png",
        # Cacheable within a session; the frontend appends a per-page-load
        # token so a reload always fetches fresh previews.
        headers={"Cache-Control": "public, max-age=3600"},
    )
