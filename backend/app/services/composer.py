from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.schemas.promotion import (
    PromotionSpec,
    CreativeDirection,
    FormatType,
    EXPORT_FORMATS,
)
from app.assets.backgrounds import get_background_for_section
from app.assets.brand import (
    BRAND_BLUE,
    BRAND_YELLOW,
    BRAND_WHITE,
    BRAND_BLACK,
    FONT_PATH_BOLD,
    FONT_PATH_EXTRABOLD,
    FONT_PATH_REGULAR,
    WASCHBAER_LOGO_PATH,
)


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _get_section_for_product(spec: PromotionSpec) -> str:
    category_map = {
        "fruta fresca": "fruta_fresca",
        "fruta": "fruta_fresca",
        "verdura": "fruta_fresca",
        "panaderia": "panaderia",
        "pan": "panaderia",
        "lacteos": "lacteos",
        "leche": "lacteos",
        "carnes": "carnes",
        "carne": "carnes",
        "bebidas": "bebidas",
        "limpieza": "limpieza",
    }
    cat = (spec.category or "").lower()
    return category_map.get(cat, "default")


def compose_promotion(
    spec: PromotionSpec,
    direction: CreativeDirection,
    format_type: FormatType,
    output_path: Path,
) -> Path:
    fmt = EXPORT_FORMATS[format_type]
    section = _get_section_for_product(spec)
    background = get_background_for_section(section, fmt.width, fmt.height)

    canvas = background.copy()
    draw = ImageDraw.Draw(canvas)

    _draw_price_band(draw, fmt.width, fmt.height)
    _draw_product_name(draw, spec.product, fmt.width, fmt.height)
    _draw_price(draw, spec.price, spec.old_price, fmt.width, fmt.height)
    _draw_validity(draw, spec.validity, fmt.width, fmt.height)

    if spec.claim:
        _draw_claim(draw, spec.claim, fmt.width, fmt.height)

    _draw_brand_bar(draw, fmt.width, fmt.height)

    if direction.waschbaer_presence in ("subtle", "graphic_accent", "featured"):
        _draw_washbaer_logo(canvas, fmt.width, fmt.height)

    canvas.save(str(output_path), quality=95)
    return output_path


def _draw_price_band(draw: ImageDraw.ImageDraw, w: int, h: int):
    band_h = h // 8
    band_y = int(h * 0.65)
    draw.rectangle([0, band_y, w, band_y + band_h], fill=BRAND_BLUE)


def _draw_product_name(draw: ImageDraw.ImageDraw, name: str, w: int, h: int):
    font_size = w // 10
    font = _load_font(FONT_PATH_BOLD, font_size)
    y_pos = int(h * 0.12)
    draw.text(
        (w // 20, y_pos),
        name.upper(),
        fill=BRAND_WHITE,
        font=font,
    )


def _draw_price(
    draw: ImageDraw.ImageDraw,
    price: str,
    old_price: str | None,
    w: int,
    h: int,
):
    font_size = w // 6
    font = _load_font(FONT_PATH_EXTRABOLD, font_size)
    y_pos = int(h * 0.68)
    x_pos = w // 20

    draw.text(
        (x_pos, y_pos),
        price,
        fill=BRAND_YELLOW,
        font=font,
        stroke_width=3,
        stroke_fill=BRAND_BLACK,
    )

    if old_price:
        old_font = _load_font(FONT_PATH_REGULAR, w // 14)
        draw.text(
            (x_pos, y_pos - old_font.size - 10),
            old_price,
            fill="#AAAAAA",
            font=old_font,
        )
        bbox = draw.textbbox((x_pos, y_pos - old_font.size - 10), old_price, font=old_font)
        draw.line(
            [(bbox[0], (bbox[1] + bbox[3]) // 2), (bbox[2], (bbox[1] + bbox[3]) // 2)],
            fill="#AAAAAA",
            width=3,
        )


def _draw_validity(draw: ImageDraw.ImageDraw, validity: str, w: int, h: int):
    font_size = w // 18
    font = _load_font(FONT_PATH_BOLD, font_size)
    text = f"⚡ {validity.upper()}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    padding = 16
    x = w // 20
    y = int(h * 0.82)
    draw.rounded_rectangle(
        [x, y, x + text_w + padding * 2, y + text_h + padding],
        radius=8,
        fill=BRAND_YELLOW,
    )
    draw.text((x + padding, y + padding // 2), text, fill=BRAND_BLACK, font=font)


def _draw_claim(draw: ImageDraw.ImageDraw, claim: str, w: int, h: int):
    font_size = w // 16
    font = _load_font(FONT_PATH_REGULAR, font_size)
    y_pos = int(h * 0.58)
    draw.text(
        (w // 20, y_pos),
        claim,
        fill=BRAND_WHITE,
        font=font,
    )


def _draw_brand_bar(draw: ImageDraw.ImageDraw, w: int, h: int):
    bar_h = h // 22
    bar_y = h - bar_h - 10
    draw.rectangle([0, bar_y, w, bar_y + bar_h], fill=BRAND_BLUE)
    font = _load_font(FONT_PATH_BOLD, bar_h - 16)
    draw.text((20, bar_y + 8), "EDEKA MÜHLENBEIN", fill=BRAND_WHITE, font=font)


def _draw_washbaer_logo(canvas: Image.Image, w: int, h: int):
    if not WASCHBAER_LOGO_PATH.exists():
        return
    logo = Image.open(WASCHBAER_LOGO_PATH).convert("RGBA")
    logo_size = int(w * 0.18)
    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
    x = w - logo_size - 20
    y = h - logo_size - 20
    canvas.paste(logo, (x, y), logo)
