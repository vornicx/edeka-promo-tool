from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.assets.brand import (
    BRAND_BLUE,
    BRAND_YELLOW,
    FONT_PATH_BOLD,
    FONT_PATH_EXTRABOLD,
)
from app.schemas.promotion import (
    CreativeDirection,
    EXPORT_FORMATS,
    FormatType,
    PromotionSpec,
)

PRODUCT_ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "product_photos"

PRODUCT_ASSETS: dict[str, list[str]] = {
    "strawberries": ["fresa", "fresas", "erdbeer", "erdbeere", "erdbeeren", "strawberry", "strawberries"],
    "apples": ["manzana", "manzanas", "apfel", "aepfel", "apple", "apples"],
    "bananas": ["platano", "platanos", "banana", "bananas", "banane", "bananen"],
    "oranges": ["naranja", "naranjas", "orange", "oranges", "orangen"],
    "grapes": ["uva", "uvas", "traube", "trauben", "grape", "grapes"],
    "tomatoes": ["tomate", "tomates", "tomato", "tomatoes", "tomaten"],
    "cucumbers": ["pepino", "pepinos", "gurke", "gurken", "cucumber", "cucumbers"],
    "carrots": ["zanahoria", "zanahorias", "karotte", "karotten", "moehre", "moehren", "mohre", "mohren", "carrot", "carrots"],
    "lettuce": ["lechuga", "salat", "kopfsalat", "lettuce"],
    "peppers": ["pimiento", "pimientos", "paprika", "bell pepper", "peppers"],
}

FRUIT_WORDS = ["fruta", "fruechte", "frucht", "obst", "fruit"]
VEGETABLE_WORDS = ["verdura", "gemuese", "gemuse", "vegetable", "vegetables"]


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

def _hex_to_rgb(hex_color: str, fallback: tuple[int, int, int] = (0, 76, 150)) -> tuple[int, int, int]:
    try:
        h = hex_color.strip().lstrip("#")
        if len(h) != 6:
            return fallback
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return fallback


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _with_alpha(rgb: tuple[int, int, int], alpha: int) -> tuple[int, int, int, int]:
    return (*rgb, alpha)


def _lighten(rgb: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return _mix(rgb, (255, 255, 255), t)


def _darken(rgb: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return _mix(rgb, (0, 0, 0), t)


# ---------------------------------------------------------------------------
# Font / text helpers
# ---------------------------------------------------------------------------

def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _fit_font_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    max_width: int,
    start_size: int,
    min_size: int,
) -> ImageFont.ImageFont:
    size = start_size
    while size > min_size:
        font = _load_font(font_path, size)
        if _text_size(draw, text, font)[0] <= max_width:
            return font
        size -= max(2, start_size // 32)
    return _load_font(font_path, min_size)


def _fit_font_height(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    max_height: int,
    start_size: int,
    min_size: int,
) -> ImageFont.ImageFont:
    size = start_size
    while size > min_size:
        font = _load_font(font_path, size)
        if _text_size(draw, text, font)[1] <= max_height:
            return font
        size -= max(2, start_size // 32)
    return _load_font(font_path, min_size)


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int = 2,
) -> list[str]:
    words = [w for w in text.replace("\n", " ").split(" ") if w]
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if _text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) == max_lines - 1:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines[:max_lines]


def _fit_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    max_width: int,
    max_height: int,
    start_size: int,
    min_size: int,
    max_lines: int = 2,
    line_spacing: float = 1.12,
) -> tuple[ImageFont.ImageFont, list[str]]:
    """Find the largest font where ``text`` wraps into <= max_lines and fits the box."""
    size = max(start_size, min_size + 1)
    step = max(2, start_size // 28)
    best: tuple[ImageFont.ImageFont, list[str]] | None = None
    while size >= min_size:
        font = _load_font(font_path, size)
        lines = _wrap_text(draw, text, font, max_width, max_lines)
        widest = max((_text_size(draw, line, font)[0] for line in lines), default=0)
        line_h = _text_size(draw, "Ág", font)[1]
        total_h = int(line_h * line_spacing * len(lines))
        if widest <= max_width and total_h <= max_height:
            best = (font, lines)
            break
        size -= step
    if best is None:
        font = _load_font(font_path, min_size)
        best = (font, _wrap_text(draw, text, font, max_width, max_lines))
    return best


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    zone_x: int,
    zone_w: int,
    y: int,
    font: ImageFont.ImageFont,
    fill,
    align: str = "center",
    line_spacing: float = 1.12,
) -> int:
    line_h = _text_size(draw, "Ág", font)[1]
    for line in lines:
        lw, _ = _text_size(draw, line, font)
        if align == "center":
            lx = zone_x + (zone_w - lw) // 2
        elif align == "right":
            lx = zone_x + zone_w - lw
        else:
            lx = zone_x
        draw.text((lx, y), line, fill=fill, font=font)
        y += int(line_h * line_spacing)
    return y


def _draw_text_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    cx: int,
    y: int,
    font: ImageFont.ImageFont,
    fill,
):
    tw, _ = _text_size(draw, text, font)
    x = int(cx - tw / 2)
    draw.text((x, y), text, fill=fill, font=font)



# ---------------------------------------------------------------------------
# Asset resolution
# ---------------------------------------------------------------------------

def _normalize(value: str | None) -> str:
    if not value:
        return ""
    clean = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return clean.lower()


def _resolve_product_asset(spec: PromotionSpec) -> Path | None:
    haystack = _normalize(f"{spec.product} {spec.category or ''}")
    for asset_name, keywords in PRODUCT_ASSETS.items():
        if any(keyword in haystack for keyword in keywords):
            path = PRODUCT_ASSET_DIR / f"{asset_name}.png"
            if path.exists():
                return path

    if any(word in haystack for word in FRUIT_WORDS):
        path = PRODUCT_ASSET_DIR / "mixed_fruit.png"
        return path if path.exists() else None
    if any(word in haystack for word in VEGETABLE_WORDS):
        path = PRODUCT_ASSET_DIR / "mixed_vegetables.png"
        return path if path.exists() else None
    return None


def _trim_alpha(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    if not bbox:
        return image
    return image.crop(bbox)


def _load_product_image(spec: PromotionSpec, max_size: tuple[int, int]) -> Image.Image | None:
    asset_path = _resolve_product_asset(spec)
    if not asset_path:
        return None
    product = _trim_alpha(Image.open(asset_path).convert("RGBA"))
    product.thumbnail(max_size, Image.Resampling.LANCZOS)
    return product


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

@dataclass
class Zone:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def cx(self) -> int:
        return self.x + self.w // 2

    @property
    def cy(self) -> int:
        return self.y + self.h // 2


def _draw_soft_shadow(canvas: Image.Image, x: int, y: int, w: int, h: int, blur: int = 20, intensity: int = 45):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse((x, y, x + w, y + h), fill=(0, 20, 55, intensity))
    blurred = layer.filter(ImageFilter.GaussianBlur(radius=blur))
    canvas.alpha_composite(blurred)


def _draw_product(canvas: Image.Image, product: Image.Image, cx: int, cy: int, angle: float = 0.0):
    if angle != 0:
        rotated = product.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    else:
        rotated = product.copy()
    x = cx - rotated.width // 2
    y = cy - rotated.height // 2
    # Soft shadow beneath the product
    sw = int(rotated.width * 0.75)
    sh = int(rotated.height * 0.12)
    sx = x + (rotated.width - sw) // 2
    sy = y + rotated.height - int(sh * 0.5)
    _draw_soft_shadow(canvas, sx, sy, sw, sh, blur=max(12, rotated.width // 25), intensity=45)
    canvas.alpha_composite(rotated, (x, y))


# ---------------------------------------------------------------------------
# Brand logo
# ---------------------------------------------------------------------------

def _draw_logo(draw: ImageDraw.ImageDraw, x: int, y: int, height: int, blue: tuple[int, int, int], yellow: tuple[int, int, int]):
    width = int(height * 2.5)
    radius = height // 5
    draw.rounded_rectangle((x, y, x + width, y + height), radius=radius, fill=blue)
    pad = int(height * 0.22)
    max_text_w = width - pad * 2
    font_size = int(height * 0.55)
    font = _fit_font_width(draw, "EDEKA", FONT_PATH_EXTRABOLD, max_text_w, font_size, int(font_size * 0.55))
    tw, th = _text_size(draw, "EDEKA", font)
    tx = x + (width - tw) // 2
    ty = y + (height - th) // 2 - 1
    draw.text((tx, ty), "EDEKA", fill=yellow, font=font)


# ---------------------------------------------------------------------------
# Discount badge
# ---------------------------------------------------------------------------

def _parse_price(value: str) -> float | None:
    clean = value.replace("€", "").replace("$", "").replace(",", ".").strip()
    try:
        return float(clean)
    except ValueError:
        return None


def _discount_percent(old: str, new: str) -> int | None:
    old_val = _parse_price(old)
    new_val = _parse_price(new)
    if not old_val or not new_val or old_val <= 0 or new_val >= old_val:
        return None
    return int(round((1 - new_val / old_val) * 100))


def _draw_discount_badge(canvas: Image.Image, percent: int, cx: int, cy: int, radius: int, blue: tuple[int, int, int]):
    draw = ImageDraw.Draw(canvas)
    # White ring + red circle
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(255, 255, 255), outline=blue, width=max(2, radius // 12))
    inner_r = int(radius * 0.85)
    draw.ellipse((cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r), fill=(211, 47, 47))
    text = f"-{percent}%"
    font = _fit_font_width(draw, text, FONT_PATH_EXTRABOLD, int(inner_r * 1.5), int(inner_r * 0.75), int(inner_r * 0.45))
    tw, th = _text_size(draw, text, font)
    draw.text((cx - tw / 2, cy - th / 2 - 1), text, fill=(255, 255, 255), font=font)


# ---------------------------------------------------------------------------
# Headline block
# ---------------------------------------------------------------------------

def _draw_headline_block(
    draw: ImageDraw.ImageDraw,
    spec: PromotionSpec,
    zone: Zone,
    color: tuple[int, int, int],
    align: str = "left",
    claim_color: tuple[int, int, int] = (90, 100, 115),
) -> int:
    """Draw product headline (up to 2 lines) plus optional claim, never truncating."""
    x, y, w, h = zone.x, zone.y, zone.w, zone.h
    max_w = int(w * 0.96)
    headline = spec.product.upper()

    # Reserve vertical room for the claim so the headline never crowds it out.
    claim_reserve = int(h * 0.34) if spec.claim else 0
    head_max_h = h - claim_reserve

    headline_font, head_lines = _fit_wrapped(
        draw, headline, FONT_PATH_EXTRABOLD, max_w, head_max_h,
        start_size=int(h * 0.62), min_size=int(h * 0.16),
        max_lines=2, line_spacing=1.05,
    )
    bottom = _draw_wrapped(
        draw, head_lines, x, w, y, headline_font, color,
        align=align, line_spacing=1.05,
    )

    if not spec.claim:
        return bottom

    cy = bottom + int(h * 0.06)
    claim_max_h = max(int(h * 0.30), (y + h) - cy)
    claim_font, claim_lines = _fit_wrapped(
        draw, spec.claim, FONT_PATH_BOLD, max_w, claim_max_h,
        start_size=int(h * 0.24), min_size=int(h * 0.10),
        max_lines=2, line_spacing=1.15,
    )
    return _draw_wrapped(
        draw, claim_lines, x, w, cy, claim_font, claim_color,
        align=align, line_spacing=1.15,
    )


# ---------------------------------------------------------------------------
# Price card
# ---------------------------------------------------------------------------

def _draw_price_card(
    canvas: Image.Image,
    spec: PromotionSpec,
    zone: Zone,
    primary: tuple[int, int, int],
    accent: tuple[int, int, int],
):
    draw = ImageDraw.Draw(canvas)
    x, y, w, h = zone.x, zone.y, zone.w, zone.h
    white = (255, 255, 255)
    radius = min(w, h) // 7

    # Soft drop shadow behind the card.
    pad = max(18, w // 30)
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)
    ldraw.rounded_rectangle(
        (pad, pad, w + pad, h + pad), radius=radius, fill=(0, 25, 60, 60)
    )
    layer = layer.filter(ImageFilter.GaussianBlur(radius=pad // 2))
    canvas.alpha_composite(layer, (x - pad, y - pad + pad // 3))

    # Card body (EDEKA-yellow) with a thin tint for crispness.
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=accent)
    draw = ImageDraw.Draw(canvas)

    pad_x = int(w * 0.09)
    pad_y = int(h * 0.10)
    ix = x + pad_x
    iy = y + pad_y
    iw = w - pad_x * 2
    bottom_limit = y + h - pad_y

    # --- Bottom band: validity pill (reserve its space first) ---
    vt = spec.validity.upper()
    pill_h = int(h * 0.16)
    validity_font = _fit_font_height(draw, vt, FONT_PATH_BOLD, int(pill_h * 0.52), int(pill_h * 0.6), int(pill_h * 0.34))
    vw, vh = _text_size(draw, vt, validity_font)
    pill_pad_x = int(pill_h * 0.45)
    pill_w = min(iw, vw + pill_pad_x * 2)
    pill_y = bottom_limit - pill_h
    pill_x = ix
    draw.rounded_rectangle(
        (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
        radius=pill_h // 2, fill=primary,
    )
    draw.text(
        (pill_x + (pill_w - vw) / 2, pill_y + (pill_h - vh) / 2 - 1),
        vt, fill=white, font=validity_font,
    )

    # --- Top band: "ANGEBOT" label (left) + struck-through old price (right) ---
    label_h = int(h * 0.14)
    label_font = _fit_font_height(draw, "ANGEBOT", FONT_PATH_EXTRABOLD, label_h, int(label_h * 1.1), int(label_h * 0.6))
    lbbox = draw.textbbox((0, 0), "ANGEBOT", font=label_font)
    draw.text((ix, iy - lbbox[1]), "ANGEBOT", fill=primary, font=label_font)
    label_bottom = iy + (lbbox[3] - lbbox[1])

    if spec.old_price:
        old_text = f"statt {spec.old_price}"
        old_font = _fit_font_height(draw, old_text, FONT_PATH_BOLD, int(label_h * 0.72), int(label_h), int(label_h * 0.45))
        obbox = draw.textbbox((0, 0), old_text, font=old_font)
        ow, oh = obbox[2] - obbox[0], obbox[3] - obbox[1]
        ox = x + w - pad_x - ow
        # baseline-align with the ANGEBOT label
        oy = label_bottom - oh
        draw.text((ox - obbox[0], oy - obbox[1]), old_text, fill=_darken(accent, 0.5), font=old_font)
        strike_y = oy + oh * 0.55
        draw.line((ox, strike_y, ox + ow, strike_y), fill=(211, 47, 47), width=max(2, h // 80))

    old_bottom = label_bottom

    # --- Middle band: the headline price, centered in remaining space ---
    price_top = old_bottom + int(h * 0.06)
    price_bottom = pill_y - int(h * 0.06)
    price_band_h = max(int(h * 0.18), price_bottom - price_top)
    price_font = _fit_font_width(draw, spec.price, FONT_PATH_EXTRABOLD, iw, int(price_band_h * 1.05), int(price_band_h * 0.45))
    price_font = _fit_font_height(draw, spec.price, FONT_PATH_EXTRABOLD, price_band_h, price_font.size, int(price_band_h * 0.40))
    bbox = draw.textbbox((0, 0), spec.price, font=price_font)
    pw = bbox[2] - bbox[0]
    px = ix + (iw - pw) // 2 - bbox[0]
    py = price_top + (price_band_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text((px, py), spec.price, fill=primary, font=price_font)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

STORE_NAME = "EDEKA MÜHLENBEIN"


def _draw_footer(
    canvas: Image.Image,
    band_h: int,
    text_color: tuple[int, int, int],
    bar_color: tuple[int, int, int] | None = None,
):
    """Draw the store name vertically centred inside a reserved bottom band."""
    draw = ImageDraw.Draw(canvas)
    w, h = canvas.size
    band_top = h - band_h
    if bar_color is not None:
        draw.rectangle((0, band_top, w, h), fill=bar_color)
    font = _fit_font_width(draw, STORE_NAME, FONT_PATH_BOLD, int(w * 0.8), int(band_h * 0.42), int(band_h * 0.22))
    tw, th = _text_size(draw, STORE_NAME, font)
    # textbbox top offset, so anchor by bbox for true vertical centring.
    bbox = draw.textbbox((0, 0), STORE_NAME, font=font)
    ty = band_top + (band_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text(((w - tw) // 2, ty), STORE_NAME, fill=text_color, font=font)


# ---------------------------------------------------------------------------
# Format-specific layouts (modern Figma/Higgsfield style)
# ---------------------------------------------------------------------------

def _layout_post(canvas: Image.Image, spec: PromotionSpec, direction: CreativeDirection, primary: tuple[int, int, int], accent: tuple[int, int, int]):
    w, h = canvas.size
    margin = int(w * 0.06)
    draw = ImageDraw.Draw(canvas)
    footer_h = int(h * 0.075)

    # Background: soft vertical gradient for a clean, modern base.
    top = _lighten(primary, 0.95)
    bottom = _lighten(primary, 0.86)
    for yy in range(h):
        draw.line((0, yy, w, yy), fill=_mix(top, bottom, yy / max(1, h - 1)))
    # Subtle accent halo behind the product (centred, fully on-canvas).
    halo_r = int(w * 0.38)
    halo_cx, halo_cy = w // 2, int(h * 0.34)
    draw.ellipse(
        (halo_cx - halo_r, halo_cy - halo_r, halo_cx + halo_r, halo_cy + halo_r),
        fill=_with_alpha(_lighten(accent, 0.25), 90),
    )

    # Logo top-left
    logo_h = int(w * 0.08)
    _draw_logo(draw, margin, margin, logo_h, primary, accent)

    # Product hero (centred, upper area)
    product_zone = Zone(margin, int(h * 0.12), w - margin * 2, int(h * 0.40))
    product = _load_product_image(spec, (int(product_zone.w * 0.78), int(product_zone.h * 0.94)))
    if product:
        _draw_product(canvas, product, product_zone.cx, product_zone.cy, angle=0.0)
    else:
        ph = int(w * 0.10)
        placeholder_font = _fit_font_width(draw, spec.product.upper(), FONT_PATH_EXTRABOLD, int(w * 0.8), ph, int(ph * 0.55))
        _draw_text_centered(draw, spec.product.upper(), product_zone.cx, product_zone.cy, placeholder_font, primary)

    # Discount badge: top-right corner, clear of logo, product and text.
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        br = int(w * 0.10)
        _draw_discount_badge(canvas, discount, w - margin - br, margin + br, br, primary)

    # Headline + claim, centred below the product.
    text_zone = Zone(margin, int(h * 0.51), w - margin * 2, int(h * 0.11))
    _draw_headline_block(draw, spec, text_zone, primary, align="center")

    # Price card, centred near the bottom.
    card_w = int(w * 0.64)
    card_h = int(h * 0.24)
    card_x = (w - card_w) // 2
    card_y = h - footer_h - int(h * 0.035) - card_h
    _draw_price_card(canvas, spec, Zone(card_x, card_y, card_w, card_h), primary, accent)

    _draw_footer(canvas, footer_h, primary)


def _layout_story(canvas: Image.Image, spec: PromotionSpec, direction: CreativeDirection, primary: tuple[int, int, int], accent: tuple[int, int, int]):
    w, h = canvas.size
    margin = int(w * 0.07)
    draw = ImageDraw.Draw(canvas)
    footer_h = int(h * 0.05)

    # Vertical gradient: light top -> tinted bottom
    top = _lighten(primary, 0.95)
    bottom = _lighten(primary, 0.80)
    for y in range(h):
        draw.line((0, y, w, y), fill=_mix(top, bottom, y / max(1, h - 1)))

    # Smooth brand-blue wave separating the product area from the text area.
    wave_y = int(h * 0.60)
    draw.polygon([(0, wave_y), (w, int(h * 0.55)), (w, h), (0, h)], fill=primary)

    # Logo top-left
    logo_h = int(w * 0.10)
    _draw_logo(draw, margin, margin, logo_h, primary, accent)

    # Product centered in upper area
    product_zone = Zone(margin, int(h * 0.13), w - margin * 2, int(h * 0.38))
    product = _load_product_image(spec, (int(product_zone.w * 0.86), int(product_zone.h * 0.92)))
    if product:
        _draw_product(canvas, product, product_zone.cx, product_zone.cy, angle=0.0)
    else:
        ph = int(w * 0.10)
        placeholder_font = _fit_font_width(draw, spec.product.upper(), FONT_PATH_EXTRABOLD, int(w * 0.85), ph, int(ph * 0.55))
        _draw_text_centered(draw, spec.product.upper(), product_zone.cx, product_zone.cy, placeholder_font, primary)

    # Discount badge: top-right corner.
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        br = int(w * 0.11)
        _draw_discount_badge(canvas, discount, w - margin - br, margin + br, br, primary)

    # Headline centered in the blue band (white text), above the price card.
    headline_zone = Zone(margin, int(h * 0.62), w - margin * 2, int(h * 0.12))
    _draw_headline_block(draw, spec, headline_zone, (255, 255, 255), align="center", claim_color=_lighten(accent, 0.2))

    # Price card centered below the headline.
    card_w = int(w * 0.72)
    card_h = int(h * 0.20)
    card_x = (w - card_w) // 2
    card_y = int(h * 0.76)
    _draw_price_card(canvas, spec, Zone(card_x, card_y, card_w, card_h), primary, accent)

    _draw_footer(canvas, footer_h, (255, 255, 255))


def _layout_poster(canvas: Image.Image, spec: PromotionSpec, direction: CreativeDirection, fmt: FormatType, primary: tuple[int, int, int], accent: tuple[int, int, int]):
    w, h = canvas.size
    margin = int(w * 0.06)
    draw = ImageDraw.Draw(canvas)
    white = (255, 255, 255)

    # Clean white background with a brand header bar and a tinted bottom panel.
    draw.rectangle((0, 0, w, h), fill=white)
    header_h = int(h * 0.06)
    draw.rectangle((0, 0, w, header_h), fill=primary)
    panel_y = int(h * 0.56)
    footer_h = int(h * 0.06)
    draw.rectangle((0, panel_y, w, h - footer_h), fill=_lighten(primary, 0.92))

    # Logo in header
    logo_h = int(header_h * 0.66)
    _draw_logo(draw, margin, (header_h - logo_h) // 2, logo_h, primary, accent)

    # Product in upper area
    product_zone = Zone(margin, int(h * 0.10), w - margin * 2, int(h * 0.42))
    product = _load_product_image(spec, (int(product_zone.w * 0.80), int(product_zone.h * 0.92)))
    if product:
        _draw_product(canvas, product, product_zone.cx, product_zone.cy, angle=0.0)
    else:
        ph = int(w * 0.10)
        placeholder_font = _fit_font_width(draw, spec.product.upper(), FONT_PATH_EXTRABOLD, int(w * 0.85), ph, int(ph * 0.55))
        _draw_text_centered(draw, spec.product.upper(), product_zone.cx, product_zone.cy, placeholder_font, primary)

    # Discount badge: top-right, below the header bar.
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        br = int(w * 0.085)
        _draw_discount_badge(canvas, discount, w - margin - br, header_h + br + int(h * 0.01), br, primary)

    # Bottom panel: headline + claim centred, price card centred beneath.
    text_zone = Zone(margin, panel_y + int(h * 0.02), w - margin * 2, int(h * 0.10))
    _draw_headline_block(draw, spec, text_zone, primary, align="center")

    card_w = int(w * 0.54)
    card_h = int(h * 0.21)
    card_x = (w - card_w) // 2
    card_y = (h - footer_h) - int(h * 0.03) - card_h
    _draw_price_card(canvas, spec, Zone(card_x, card_y, card_w, card_h), primary, accent)

    _draw_footer(canvas, footer_h, white, bar_color=primary)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compose_promotion(
    spec: PromotionSpec,
    direction: CreativeDirection,
    format_type: FormatType,
    output_path: Path,
) -> Path:
    fmt = EXPORT_FORMATS[format_type]
    canvas = Image.new("RGBA", (fmt.width, fmt.height), (255, 255, 255, 255))

    palette = direction.palette or [BRAND_BLUE, BRAND_YELLOW]
    base_hex = palette[0] if palette[0] and palette[0].startswith("#") else BRAND_BLUE
    accent_hex = palette[1] if len(palette) > 1 and palette[1].startswith("#") else BRAND_YELLOW

    primary = _hex_to_rgb(base_hex, _hex_to_rgb(BRAND_BLUE))
    accent = _hex_to_rgb(accent_hex, _hex_to_rgb(BRAND_YELLOW))
    # Keep close to EDEKA identity
    primary = _mix(primary, _hex_to_rgb(BRAND_BLUE), 0.30)
    accent = _mix(accent, _hex_to_rgb(BRAND_YELLOW), 0.40)

    if format_type == FormatType.POST:
        _layout_post(canvas, spec, direction, primary, accent)
    elif format_type == FormatType.STORY:
        _layout_story(canvas, spec, direction, primary, accent)
    else:
        _layout_poster(canvas, spec, direction, format_type, primary, accent)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(str(output_path), quality=96, optimize=True)
    return output_path
