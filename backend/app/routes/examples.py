"""On-demand example previews so the user can pick style/tone/level visually."""
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Response

from app.schemas.promotion import (
    CreativeDirection,
    DifferentiationLevel,
    FormatType,
    PromotionSpec,
    ToneType,
)
from app.services.composer import compose_promotion

router = APIRouter(prefix="/api/examples", tags=["examples"])

_TONES = {t.value for t in ToneType}
_LEVELS = {d.value for d in DifferentiationLevel}
_STYLES = {"edeka", "kreativ"}

# In-memory cache (per process): regenerates on each app start, so it never
# goes stale after a design/code update.
_cache: dict[str, bytes] = {}


def _render(style: str, tone: str, level: str) -> bytes:
    spec = PromotionSpec(
        product="Erdbeeren",
        category="Obst",
        price="2,99 €",
        old_price="3,49 €",
        validity="KW 24",
        origin="aus der Region",
        claim="saftig & fruchtig",
        product_image="builtin:strawberries",
        style=style,
        tone=tone,
        differentiation_level=level,
        format=FormatType.POST,
    )
    palette = ["#004C96", "#FFD600"] if style == "edeka" else ["#1565C0", "#FFA000"]
    direction = CreativeDirection(
        name="beispiel", intent="", composition="", palette=palette,
        text_safe_area="bottom", boldness="high", waschbaer_presence="featured",
    )
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        compose_promotion(spec, direction, FormatType.POST, Path(tmp))
        return Path(tmp).read_bytes()
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


@router.get("")
async def example(style: str = "edeka", tone: str = "fresco", level: str = "medio"):
    style = style.lower() if style.lower() in _STYLES else "edeka"
    tone = tone.lower() if tone.lower() in _TONES else "fresco"
    level = level.lower() if level.lower() in _LEVELS else "medio"

    key = f"{style}__{tone}__{level}"
    if key not in _cache:
        _cache[key] = _render(style, tone, level)
    return Response(content=_cache[key], media_type="image/png")
