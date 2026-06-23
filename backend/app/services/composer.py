from __future__ import annotations

import colorsys
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
    FONT_PATH_REGULAR,
    FONT_PATH_SEMIBOLD,
    WASCHBAER_LOGO_PATH,
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


def _hsv_adjust(rgb: tuple[int, int, int], sat: float = 1.0, val: float = 1.0) -> tuple[int, int, int]:
    h, s, v = colorsys.rgb_to_hsv(*[c / 255 for c in rgb])
    s = max(0.0, min(1.0, s * sat))
    v = max(0.0, min(1.0, v * val))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


_DOMINANT_CACHE: dict[str, tuple[int, int, int]] = {}


def _product_dominant_color(asset_path: Path | None) -> tuple[int, int, int] | None:
    """Saturation-weighted average colour of the opaque product pixels."""
    if not asset_path:
        return None
    key = str(asset_path)
    if key in _DOMINANT_CACHE:
        return _DOMINANT_CACHE[key]
    try:
        img = Image.open(asset_path).convert("RGBA")
    except Exception:  # noqa: BLE001
        return None
    img.thumbnail((72, 72), Image.Resampling.LANCZOS)
    tr = tg = tb = wsum = 0.0
    for r, g, b, a in img.getdata():
        if a < 180:
            continue
        _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if v < 0.15:
            continue
        w = 0.15 + s  # favour vivid pixels, but keep some weight for all
        tr += r * w
        tg += g * w
        tb += b * w
        wsum += w
    if wsum <= 0:
        return None
    color = (int(tr / wsum), int(tg / wsum), int(tb / wsum))
    _DOMINANT_CACHE[key] = color
    return color


# ---------------------------------------------------------------------------
# Gradients / glows (small build + upscale for speed)
# ---------------------------------------------------------------------------

def _vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    for y in range(h):
        px[0, y] = _mix(top, bottom, y / max(1, h - 1))
    return strip.resize((w, h))


def _diagonal_gradient(size: tuple[int, int], c1: tuple[int, int, int], c2: tuple[int, int, int]) -> Image.Image:
    """Smooth top-left -> bottom-right gradient via a small upscaled tile."""
    n = 64
    tile = Image.new("RGB", (n, n))
    px = tile.load()
    for y in range(n):
        for x in range(n):
            t = (x + y) / (2 * (n - 1))
            px[x, y] = _mix(c1, c2, t)
    return tile.resize(size, Image.BILINEAR)


def _radial_alpha(diam: int, inner: int, outer: int, falloff: float = 1.0) -> Image.Image:
    g = Image.new("L", (diam, diam), 0)
    px = g.load()
    c = diam / 2
    for y in range(diam):
        for x in range(diam):
            d = min(1.0, (((x - c) ** 2 + (y - c) ** 2) ** 0.5) / c)
            px[x, y] = int(inner + (outer - inner) * (d ** falloff))
    return g


def _draw_spotlight(canvas: Image.Image, cx: int, cy: int, radius: int, color: tuple[int, int, int], max_alpha: int, falloff: float = 1.7):
    size = radius * 2
    mask = _radial_alpha(220, max_alpha, 0, falloff).resize((size, size))
    layer = Image.new("RGBA", (size, size), (*color, 0))
    layer.putalpha(mask)
    canvas.alpha_composite(layer, (cx - radius, cy - radius))


def _fill_gradient_shape(canvas: Image.Image, points, top: tuple[int, int, int], bottom: tuple[int, int, int], scale: int = 4):
    """Fill a polygon with a vertical gradient (anti-aliased mask)."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, miny = int(min(xs)) - 1, int(min(ys)) - 1
    maxx, maxy = int(max(xs)) + 1, int(max(ys)) + 1
    w, h = max(1, maxx - minx), max(1, maxy - miny)
    grad = _vertical_gradient((w, h), top, bottom).convert("RGBA")
    mask = Image.new("L", (w * scale, h * scale), 0)
    md = ImageDraw.Draw(mask)
    sp = [((px - minx) * scale, (py - miny) * scale) for px, py in points]
    md.polygon(sp, fill=255)
    grad.putalpha(mask.resize((w, h), Image.LANCZOS))
    canvas.alpha_composite(grad, (minx, miny))


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


def _resolve_builtin_asset(spec: PromotionSpec) -> Path | None:
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


def _resolve_product_asset(spec: PromotionSpec) -> Path | None:
    choice = (spec.product_image or "").strip()

    # Explicit choice from the form's motif picker.
    if choice.startswith("builtin:"):
        path = PRODUCT_ASSET_DIR / f"{choice.split(':', 1)[1]}.png"
        if path.exists():
            return path
    elif choice.startswith("custom:"):
        try:
            from app.product_library import get_product_file

            p = get_product_file(choice.split(":", 1)[1])
            if p:
                return p
        except Exception:  # noqa: BLE001
            pass

    # Auto (default): user-uploaded products take precedence over bundled ones.
    if not choice or choice == "auto":
        try:
            from app.product_library import resolve_custom_asset

            custom = resolve_custom_asset(spec.product, spec.category)
            if custom:
                return custom
        except Exception:  # noqa: BLE001 - never let the library break composing
            pass

    return _resolve_builtin_asset(spec)


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
    # Scale to FILL the target box (up or down), preserving aspect, so the
    # product is never left tiny inside a large zone.
    mw, mh = max_size
    scale = min(mw / product.width, mh / product.height)
    new_size = (max(1, round(product.width * scale)), max(1, round(product.height * scale)))
    return product.resize(new_size, Image.Resampling.LANCZOS)


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
# Knaller elements: starburst price seal, formatted price, tags, bands
# ---------------------------------------------------------------------------

RED = (226, 0, 26)  # EDEKA-style action red


def _aa_polygon(canvas: Image.Image, points, fill, outline=None, width: int = 0, scale: int = 4):
    """Composite an anti-aliased polygon by rendering supersampled in its bbox."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, miny = int(min(xs)) - 2, int(min(ys)) - 2
    maxx, maxy = int(max(xs)) + 2, int(max(ys)) + 2
    w, h = max(1, maxx - minx), max(1, maxy - miny)
    layer = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sp = [((px - minx) * scale, (py - miny) * scale) for px, py in points]
    d.polygon(sp, fill=fill, outline=outline, width=(width * scale if width else 0))
    layer = layer.resize((w, h), Image.LANCZOS)
    canvas.alpha_composite(layer, (minx, miny))


def _circle_points(cx: float, cy: float, radius: float, n: int = 72):
    return [(cx + radius * math.cos(2 * math.pi * i / n), cy + radius * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _star_points(cx: float, cy: float, outer: float, inner: float, points: int, rot: float = 0.0):
    pts = []
    for i in range(points * 2):
        r = outer if i % 2 == 0 else inner
        a = rot + math.pi * i / points
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _split_price(value: str) -> tuple[str, str, str]:
    """'2,99 €' -> ('2', '99', '€')."""
    cur = "€" if "€" in value else ("$" if "$" in value else "")
    clean = value.replace("€", "").replace("$", "").strip()
    for sep in (",", "."):
        if sep in clean:
            euros, cents = clean.split(sep, 1)
            return euros.strip() or "0", (cents.strip() + "00")[:2], cur
    return clean or "0", "", cur


def _draw_price_value(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    max_w: int,
    max_h: int,
    price: str,
    color: tuple[int, int, int],
):
    """Big euros + superscript cents + small currency, centred on (cx, cy)."""
    euros, cents, cur = _split_price(price)
    size = max_h
    while size > 12:
        euros_font = _load_font(FONT_PATH_EXTRABOLD, size)
        small = max(10, int(size * 0.44))
        cents_font = _load_font(FONT_PATH_EXTRABOLD, small)
        cur_font = _load_font(FONT_PATH_BOLD, max(10, int(size * 0.40)))
        eb = draw.textbbox((0, 0), euros, font=euros_font)
        ew, eh = eb[2] - eb[0], eb[3] - eb[1]
        gap = max(4, int(size * 0.05))
        cb = draw.textbbox((0, 0), cents or "00", font=cents_font)
        cw = (cb[2] - cb[0]) if cents else 0
        ub = draw.textbbox((0, 0), cur, font=cur_font)
        uw = (ub[2] - ub[0]) if cur else 0
        tail = max(cw, uw)
        group_w = ew + (gap + tail if (cents or cur) else 0)
        if group_w <= max_w and eh <= max_h:
            break
        size -= max(2, size // 24)

    left = cx - group_w // 2
    top = cy - eh // 2
    # Euros (big)
    draw.text((left - eb[0], top - eb[1]), euros, fill=color, font=euros_font)
    tail_x = left + ew + gap
    if cents:
        # cents raised to the top of the euros block (superscript)
        draw.text((tail_x - cb[0], top - cb[1]), cents, fill=color, font=cents_font)
    if cur:
        # currency sits at the lower portion, under the cents
        cur_y = top + eh - (ub[3] - ub[1])
        draw.text((tail_x - ub[0], cur_y - ub[1]), cur, fill=color, font=cur_font)


def _draw_price_star(
    canvas: Image.Image,
    spec: PromotionSpec,
    cx: int,
    cy: int,
    radius: int,
    primary: tuple[int, int, int],
    accent: tuple[int, int, int],
    rot_deg: float = -8.0,
):
    """The classic 'Knallerpreis' star seal with the big price inside."""
    draw = ImageDraw.Draw(canvas)
    white = (255, 255, 255)
    rot = math.radians(rot_deg)
    n = 15

    # Soft shadow under the star.
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse((cx - radius, cy - radius + int(radius * 0.18), cx + radius, cy + radius + int(radius * 0.18)),
               fill=(0, 20, 50, 70))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=max(8, radius // 12))))

    # Layered star: blue rim -> white -> gradient-yellow core (depth).
    _aa_polygon(canvas, _star_points(cx, cy, radius, radius * 0.80, n, rot), fill=primary)
    _aa_polygon(canvas, _star_points(cx, cy, radius * 0.93, radius * 0.74, n, rot), fill=white)
    _fill_gradient_shape(
        canvas, _star_points(cx, cy, radius * 0.86, radius * 0.68, n, rot),
        top=_lighten(accent, 0.30), bottom=_darken(accent, 0.18),
    )
    # Inner glossy highlight (upper third) for a 3D pop.
    _draw_spotlight(canvas, cx, cy - int(radius * 0.22), int(radius * 0.55), (255, 255, 255), 90, falloff=1.6)
    draw = ImageDraw.Draw(canvas)

    inner = int(radius * 0.66)
    # "statt" struck-through old price at the upper area.
    top_cursor = cy - int(inner * 0.78)
    if spec.old_price:
        old_text = f"statt {spec.old_price}"
        of = _fit_font_width(draw, old_text, FONT_PATH_BOLD, int(inner * 1.5), int(radius * 0.16), int(radius * 0.09))
        ob = draw.textbbox((0, 0), old_text, font=of)
        ow, oh = ob[2] - ob[0], ob[3] - ob[1]
        ox = cx - ow // 2
        draw.text((ox - ob[0], top_cursor - ob[1]), old_text, fill=_darken(primary, 0.15), font=of)
        draw.line((ox, top_cursor + oh * 0.5, ox + ow, top_cursor + oh * 0.5), fill=RED, width=max(3, radius // 40))
        price_cy = cy + int(radius * 0.06)
        price_h = int(radius * 0.62)
    else:
        price_cy = cy
        price_h = int(radius * 0.78)

    _draw_price_value(draw, cx, price_cy, int(inner * 1.7), price_h, spec.price, primary)


def _draw_price_disc(
    canvas: Image.Image,
    spec: PromotionSpec,
    cx: int,
    cy: int,
    radius: int,
    fill: tuple[int, int, int],
    text_color: tuple[int, int, int],
    ring: tuple[int, int, int] | None = None,
    gradient: tuple[tuple[int, int, int], tuple[int, int, int]] | None = None,
):
    """Clean round price seal (no spikes) for the editorial Kreativ style."""
    draw = ImageDraw.Draw(canvas)
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse((cx - radius, cy - radius + int(radius * 0.16), cx + radius, cy + radius + int(radius * 0.16)),
               fill=(0, 0, 0, 65))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=max(8, radius // 10))))

    if ring is not None:
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=ring)
        ri = int(radius * 0.9)
    else:
        ri = radius
    if gradient:
        _fill_gradient_shape(canvas, _circle_points(cx, cy, ri), top=gradient[0], bottom=gradient[1])
        draw = ImageDraw.Draw(canvas)
    else:
        draw.ellipse((cx - ri, cy - ri, cx + ri, cy + ri), fill=fill)

    top_cursor = cy - int(ri * 0.64)
    if spec.old_price:
        old_text = f"statt {spec.old_price}"
        of = _fit_font_width(draw, old_text, FONT_PATH_BOLD, int(ri * 1.4), int(radius * 0.17), int(radius * 0.1))
        ob = draw.textbbox((0, 0), old_text, font=of)
        ow, oh = ob[2] - ob[0], ob[3] - ob[1]
        ox = cx - ow // 2
        draw.text((ox - ob[0], top_cursor - ob[1]), old_text, fill=text_color, font=of)
        draw.line((ox, top_cursor + oh * 0.5, ox + ow, top_cursor + oh * 0.5), fill=RED, width=max(3, radius // 38))
        price_cy = cy + int(radius * 0.08)
        price_h = int(ri * 0.58)
    else:
        price_cy = cy
        price_h = int(ri * 0.76)
    _draw_price_value(draw, cx, price_cy, int(ri * 1.5), price_h, spec.price, text_color)


def _draw_discount_burst(canvas: Image.Image, percent: int, cx: int, cy: int, radius: int):
    """Small red explosion badge for the discount percentage."""
    white = (255, 255, 255)
    _aa_polygon(canvas, _star_points(cx, cy, radius, radius * 0.72, 12, rot=0.2), fill=white)
    _aa_polygon(canvas, _star_points(cx, cy, radius * 0.88, radius * 0.62, 12, rot=0.2), fill=RED)
    draw = ImageDraw.Draw(canvas)
    text = f"-{percent}%"
    font = _fit_font_width(draw, text, FONT_PATH_EXTRABOLD, int(radius * 1.25), int(radius * 0.8), int(radius * 0.4))
    b = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (b[2] - b[0]) / 2 - b[0], cy - (b[3] - b[1]) / 2 - b[1]), text, fill=white, font=font)


def _draw_tag(
    canvas: Image.Image,
    text: str,
    cx: int,
    cy: int,
    height: int,
    bg: tuple[int, int, int],
    fg: tuple[int, int, int],
    angle: float = 0.0,
):
    """A small rounded banner/label, optionally rotated, centred on (cx, cy)."""
    text = text.upper()
    pad_x = int(height * 0.5)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    font = _fit_font_height(tmp, text, FONT_PATH_BOLD, int(height * 0.5), int(height * 0.6), int(height * 0.3))
    b = tmp.textbbox((0, 0), text, font=font)
    tw, th = b[2] - b[0], b[3] - b[1]
    w = tw + pad_x * 2
    layer = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((0, 0, w, height), radius=height // 2, fill=bg)
    ld.text(((w - tw) / 2 - b[0], (height - th) / 2 - b[1]), text, fill=fg, font=font)
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def _draw_diagonal_band(
    canvas: Image.Image,
    top_left: int,
    top_right: int,
    height: int,
    color: tuple[int, int, int],
    at_bottom: bool = False,
):
    """Full-width band with a slanted edge (top_left/top_right give the slant)."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    if at_bottom:
        y0 = h - height
        pts = [(0, h), (w, h), (w, y0 + top_right), (0, y0 + top_left)]
    else:
        pts = [(0, 0), (w, 0), (w, top_right), (0, top_left)]
    draw.polygon(pts, fill=color)


# ---------------------------------------------------------------------------
# Shared Knaller scaffolding
# ---------------------------------------------------------------------------

STORE_NAME = "EDEKA MÜHLENBEIN"
SLOGAN = "Wir lieben Lebensmittel."
INSTAGRAM = "@waschbaer_edeka"
GREEN = (60, 140, 46)  # BIO tag


def _paint_background(canvas: Image.Image, cfg: "StyleConfig"):
    w, h = canvas.size
    # Saturated EDEKA-blue diagonal gradient base.
    top = _lighten(cfg.primary, cfg.bg_light)
    bottom = _darken(cfg.primary, cfg.bg_dark)
    canvas.paste(_diagonal_gradient((w, h), top, bottom), (0, 0))

    # Soft vignette at the corners for depth (no hard shapes).
    if cfg.vignette > 0:
        vig = Image.new("RGBA", (w, h), (*_darken(cfg.primary, 0.5), 0))
        vig.putalpha(_radial_alpha(240, 0, cfg.vignette, falloff=2.4).resize((w, h)))
        canvas.alpha_composite(vig)


def _load_mascot(target_h: int) -> Image.Image | None:
    if not WASCHBAER_LOGO_PATH.exists():
        return None
    logo = _trim_alpha(Image.open(WASCHBAER_LOGO_PATH).convert("RGBA"))
    ratio = target_h / max(1, logo.height)
    return logo.resize((max(1, int(logo.width * ratio)), target_h), Image.Resampling.LANCZOS)


def _draw_brand_lockup(canvas: Image.Image, x: int, y: int, mascot_h: int, accent: tuple[int, int, int],
                       sub_color: tuple[int, int, int] = (255, 255, 255), halo: bool = True):
    """The Waschbär mascot + EDEKA wordmark — the store's brand mark, top-left."""
    draw = ImageDraw.Draw(canvas)
    text_x = x
    mascot = _load_mascot(mascot_h)
    if mascot is not None:
        if halo:  # soft halo so the dark mascot reads on a dark background
            _draw_spotlight(canvas, x + mascot.width // 2, y + mascot_h // 2, int(mascot_h * 0.75), (255, 255, 255), 70)
        canvas.alpha_composite(mascot, (x, y))
        text_x = x + mascot.width + int(mascot_h * 0.14)

    ed_h = int(mascot_h * 0.48)
    ed_font = _load_font(FONT_PATH_EXTRABOLD, ed_h)
    eb = draw.textbbox((0, 0), "EDEKA", font=ed_font)
    sub = "Mühlenbein"
    sub_font = _load_font(FONT_PATH_BOLD, int(mascot_h * 0.27))
    sbb = draw.textbbox((0, 0), sub, font=sub_font)
    gap = int(mascot_h * 0.10)
    block_h = (eb[3] - eb[1]) + gap + (sbb[3] - sbb[1])
    ty = y + (mascot_h - block_h) // 2
    draw.text((text_x - eb[0], ty - eb[1]), "EDEKA", fill=accent, font=ed_font)
    ty2 = ty + (eb[3] - eb[1]) + gap
    draw.text((text_x - sbb[0], ty2 - sbb[1]), sub, fill=sub_color, font=sub_font)


def _draw_angebot_badge(canvas: Image.Image, cx: int, cy: int, height: int, accent: tuple[int, int, int], primary: tuple[int, int, int]):
    _draw_tag(canvas, "ANGEBOT", cx, cy, height, accent, primary, angle=-7.0)


def _draw_footer_text(canvas: Image.Image, accent: tuple[int, int, int], margin: int):
    """Store name + slogan + IG handle, centred near the bottom on the blue bg."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    band_top = h - int(h * 0.085)
    draw.line((margin, band_top, w - margin, band_top), fill=accent, width=max(2, h // 650))
    avail = h - band_top

    name_font = _fit_font_width(draw, STORE_NAME, FONT_PATH_EXTRABOLD, int(w * 0.82), int(avail * 0.38), int(avail * 0.22))
    nb = draw.textbbox((0, 0), STORE_NAME, font=name_font)
    nh = nb[3] - nb[1]
    sub = f"{SLOGAN}   ·   {INSTAGRAM}"
    sub_font = _fit_font_width(draw, sub, FONT_PATH_BOLD, int(w * 0.88), int(avail * 0.24), int(avail * 0.12))
    sbb = draw.textbbox((0, 0), sub, font=sub_font)
    sh = sbb[3] - sbb[1]
    gap = int(avail * 0.14)
    ny = band_top + (avail - (nh + gap + sh)) // 2
    draw.text(((w - (nb[2] - nb[0])) // 2 - nb[0], ny - nb[1]), STORE_NAME, fill=(255, 255, 255), font=name_font)
    sy = ny + nh + gap
    draw.text(((w - (sbb[2] - sbb[0])) // 2 - sbb[0], sy - sbb[1]), sub, fill=accent, font=sub_font)


def _draw_product_or_name(canvas, draw, spec, product_zone, name_color):
    product = _load_product_image(spec, (int(product_zone.w * 0.96), int(product_zone.h * 0.96)))
    if product:
        _draw_product(canvas, product, product_zone.cx, product_zone.cy, angle=0.0)
    else:
        ph = int(product_zone.w * 0.16)
        f = _fit_font_width(draw, spec.product.upper(), FONT_PATH_EXTRABOLD, int(product_zone.w * 0.85), ph, int(ph * 0.55))
        _draw_text_centered(draw, spec.product.upper(), product_zone.cx, product_zone.cy, f, name_color)


def _draw_validity_tag(canvas, spec, cx, cy, height, accent, primary):
    txt = spec.validity if spec.validity.lower().startswith(("nur", "bis", "kw", "gültig")) else f"nur {spec.validity}"
    _draw_tag(canvas, txt, cx, cy, height, accent, primary, angle=-3.0)


def _context_tags(spec: PromotionSpec) -> list[tuple[str, tuple[int, int, int], tuple[int, int, int]]]:
    """Derive realistic flyer badges (BIO / AUS DER REGION / NEU) from the spec."""
    hay = _normalize(f"{spec.product} {spec.category or ''} {spec.claim or ''} {spec.origin or ''}")
    white = (255, 255, 255)
    tags: list[tuple[str, tuple[int, int, int], tuple[int, int, int]]] = []
    if "bio" in hay or "oekolog" in hay or "organic" in hay:
        tags.append(("BIO", GREEN, white))
    if spec.origin or "region" in hay or "heimat" in hay or "lokal" in hay:
        tags.append(("AUS DER REGION", RED, white))
    if "neu" in hay or "new" in hay:
        tags.append(("NEU", RED, white))
    return tags[:2]


def _tag_width(text: str, height: int) -> int:
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    font = _fit_font_height(tmp, text.upper(), FONT_PATH_BOLD, int(height * 0.5), int(height * 0.6), int(height * 0.3))
    b = tmp.textbbox((0, 0), text.upper(), font=font)
    return (b[2] - b[0]) + int(height * 0.5) * 2


def _draw_context_tags(canvas: Image.Image, spec: PromotionSpec, x_left: int, y_top: int, height: int, angle: float = -4.0, force_region: bool = False):
    """Stack up to two contextual badges, top-left anchored."""
    tags = _context_tags(spec)
    if force_region and not any(t[0] == "AUS DER REGION" for t in tags):
        tags.insert(0, ("AUS DER REGION", RED, (255, 255, 255)))
        tags = tags[:2]
    y = y_top
    for text, bg, fg in tags:
        tw = _tag_width(text, height)
        _draw_tag(canvas, text, x_left + tw // 2, y + height // 2, height, bg, fg, angle=angle)
        y += int(height * 1.28)


# ---------------------------------------------------------------------------
# Format-specific layouts (German 'Knaller' style)
# ---------------------------------------------------------------------------

CLAIM_LIGHT = (205, 222, 245)

GOLD = (206, 167, 78)


def _kreativ_palette(spec: PromotionSpec):
    """Dark-luxe palette: deep background, warm-white ink, a metal/colour accent
    and a product-coloured glow. Returns (accent, ink, bg, glow)."""
    tone = _enum_val(spec.tone)
    base = _product_dominant_color(_resolve_product_asset(spec)) or _hex_to_rgb("#1565C0")
    glow = _hsv_adjust(base, sat=1.1, val=1.0)
    ink = (244, 241, 234)               # warm white

    if tone == "premium":
        accent = GOLD
        bg = (13, 13, 15)
    elif tone == "atrevido":            # accent = the vivid product colour
        accent = _hsv_adjust(base, sat=1.35, val=1.0)
        bg = (16, 15, 17)
    elif tone == "local":               # warm copper
        accent = (198, 138, 82)
        bg = (20, 16, 13)
    else:                               # fresco -> gold
        accent = GOLD
        bg = (17, 17, 20)

    return accent, ink, bg, glow


def _center_text(draw, cx, y, text, font, fill) -> int:
    b = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (b[2] - b[0]) // 2 - b[0], y - b[1]), text, fill=fill, font=font)
    return y + (b[3] - b[1])


def _draw_kicker(draw, x, y, text, height, color):
    """Small uppercase, letter-spaced label (editorial kicker)."""
    text = text.upper()
    font = _load_font(FONT_PATH_SEMIBOLD, height)
    cx = x
    for ch in text:
        b = draw.textbbox((0, 0), ch, font=font)
        draw.text((cx - b[0], y - b[1]), ch, fill=color, font=font)
        cx += (b[2] - b[0]) + max(2, int(height * (0.32 if ch == " " else 0.22)))
    return cx


def _kicker_width(draw, text, height) -> int:
    font = _load_font(FONT_PATH_SEMIBOLD, height)
    total = 0
    for ch in text.upper():
        b = draw.textbbox((0, 0), ch, font=font)
        total += (b[2] - b[0]) + max(2, int(height * (0.32 if ch == " " else 0.22)))
    return total


def _layout_luxe(canvas: Image.Image, spec: PromotionSpec, fmt: FormatType):
    """Dark-luxe style: deep background, the product spotlit, warm-white type,
    a metal/colour accent and a refined round price seal."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    tall = h / w > 1.12
    margin = int(w * 0.08)
    accent, ink, bg, glow = _kreativ_palette(spec)
    muted = _mix(ink, bg, 0.5)

    # Deep background with a faint product-tinted top and darker base + vignette.
    canvas.paste(_vertical_gradient((w, h), _mix(bg, glow, 0.08), _darken(bg, 0.4)), (0, 0))
    vig = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vig.putalpha(_radial_alpha(240, 0, 150, falloff=2.2).resize((w, h)))
    canvas.alpha_composite(vig)
    draw = ImageDraw.Draw(canvas)

    if tall:
        pz = Zone(margin, int(h * 0.14), w - margin * 2, int(h * 0.34))
        price_cx, price_cy, price_r = int(w * 0.72), int(h * 0.585), int(w * 0.185)
        head_y = int(h * 0.70)
    else:
        pz = Zone(margin, int(h * 0.15), w - margin * 2, int(h * 0.40))
        price_cx, price_cy, price_r = int(w * 0.78), int(h * 0.70), int(w * 0.16)
        head_y = int(h * 0.64)

    # Spotlight: product-coloured glow + warm white core so the product pops.
    _draw_spotlight(canvas, pz.cx, pz.cy, int(pz.w * 0.62), glow, 120, falloff=1.9)
    _draw_spotlight(canvas, pz.cx, pz.cy, int(pz.w * 0.42), (255, 248, 232), 95, falloff=1.8)
    sw, sh_h = int(pz.w * 0.42), int(pz.h * 0.05)
    _draw_soft_shadow(canvas, pz.cx - sw // 2, int(pz.cy + pz.h * 0.34), sw, sh_h,
                      blur=max(16, pz.w // 14), intensity=110)
    _draw_product_or_name(canvas, draw, spec, pz, ink)

    # Brand lockup top-left (gold wordmark, mascot with halo on the dark bg).
    _draw_brand_lockup(canvas, margin, int(h * 0.055), int(h * (0.06 if tall else 0.078)), accent,
                       sub_color=muted, halo=True)
    # "ANGEBOT" kicker, top-right.
    kh = int(h * 0.02)
    _draw_kicker(draw, w - margin - _kicker_width(draw, "ANGEBOT", kh), int(h * 0.07), "ANGEBOT", kh, accent)

    # Headline block, left: thin accent rule + product name + claim.
    draw.rectangle((margin, head_y, margin + int(w * 0.085), head_y + max(3, int(h * 0.006))), fill=accent)
    ny = head_y + int(h * 0.022)
    name_font, name_lines = _fit_wrapped(draw, spec.product.upper(), FONT_PATH_EXTRABOLD,
                                         int(w * 0.55), int(h * 0.16), int(h * 0.066), int(h * 0.034),
                                         max_lines=2, line_spacing=1.04)
    ny = _draw_wrapped(draw, name_lines, margin, int(w * 0.55), ny, name_font, ink, align="left", line_spacing=1.04)
    if spec.claim:
        cf = _load_font(FONT_PATH_REGULAR, int(h * 0.026))
        for line in _wrap_text(draw, spec.claim, cf, int(w * 0.5), 2):
            b = draw.textbbox((0, 0), line, font=cf)
            draw.text((margin - b[0], ny + int(h * 0.012) - b[1]), line, fill=muted, font=cf)
            ny += int((b[3] - b[1]) * 1.3)

    # Context badge (BIO / Region), small spaced caps under the headline.
    ctx = _context_tags(spec)
    if ctx:
        ck = int(h * 0.016)
        _draw_kicker(draw, margin, ny + int(h * 0.02), ctx[0][0], ck, accent)

    # Refined round price seal: gold ring, deep fill, warm-white price.
    discount = _discount_percent(spec.old_price or "", spec.price)
    _draw_luxe_price(canvas, spec, price_cx, price_cy, price_r, accent, ink, _darken(bg, 0.25), muted)
    if discount:
        dk = int(h * 0.02)
        dt = f"−{discount}%"
        _draw_kicker(draw, int(price_cx - _kicker_width(draw, dt, dk) / 2), int(price_cy - price_r * 1.18), dt, dk, accent)

    # Tiny footer.
    foot = f"{STORE_NAME}   ·   {INSTAGRAM}"
    foot_font = _load_font(FONT_PATH_REGULAR, int(h * 0.016))
    fb = draw.textbbox((0, 0), foot, font=foot_font)
    draw.text(((w - (fb[2] - fb[0])) // 2 - fb[0], h - int(h * 0.05) - fb[1]), foot, fill=muted, font=foot_font)


def _draw_luxe_price(canvas, spec, cx, cy, r, accent, ink, fill, muted):
    """Round price seal with a thin gold ring and clean type (no spikes)."""
    draw = ImageDraw.Draw(canvas)
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - r, cy - r + int(r * 0.12), cx + r, cy + r + int(r * 0.12)), fill=(0, 0, 0, 110))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=max(8, r // 9))))
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=accent)
    ri = int(r * 0.93)
    draw.ellipse((cx - ri, cy - ri, cx + ri, cy + ri), fill=fill)

    y = cy - int(ri * 0.5)
    if spec.old_price:
        ot = f"statt {spec.old_price}"
        of = _fit_font_width(draw, ot, FONT_PATH_REGULAR, int(ri * 1.3), int(r * 0.2), int(r * 0.12))
        ob = draw.textbbox((0, 0), ot, font=of)
        ow = ob[2] - ob[0]
        ox = cx - ow // 2
        draw.text((ox - ob[0], y - ob[1]), ot, fill=muted, font=of)
        draw.line((ox, y + (ob[3] - ob[1]) * 0.55, ox + ow, y + (ob[3] - ob[1]) * 0.55), fill=muted, width=max(2, r // 40))
        py = cy + int(r * 0.06)
    else:
        py = cy
    pf = _fit_font_width(draw, spec.price, FONT_PATH_BOLD, int(ri * 1.45), int(r * 0.5), int(r * 0.3))
    _center_text(draw, cx, py - draw.textbbox((0, 0), spec.price, font=pf)[3] // 2, spec.price, pf, ink)
    vt = spec.validity.upper()
    vf = _fit_font_width(draw, vt, FONT_PATH_SEMIBOLD, int(ri * 1.3), int(r * 0.16), int(r * 0.1))
    _center_text(draw, cx, cy + int(ri * 0.5), vt, vf, accent)


def _product_accent(spec: PromotionSpec) -> tuple[int, int, int]:
    return _hsv_adjust(_product_dominant_color(_resolve_product_asset(spec)) or _hex_to_rgb("#1565C0"), 1.2, 0.95)


def _layout_editorial(canvas: Image.Image, spec: PromotionSpec, fmt: FormatType):
    """Light editorial style: airy background, product on a big colour disc that
    bleeds off the corner, dark oversized headline, clean round price seal."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    tall = h / w > 1.12
    accent = _product_accent(spec)
    ink = (32, 32, 36)
    bg = _lighten(accent, 0.90)
    muted = _mix(ink, bg, 0.42)
    white = (255, 255, 255)
    margin = int(w * 0.075)

    canvas.paste(_vertical_gradient((w, h), _lighten(bg, 0.5), _darken(bg, 0.05)), (0, 0))

    if tall:
        disc_cx, disc_cy, disc_r = int(w * 0.74), int(h * 0.18), int(w * 0.62)
        prod = Zone(int(w * 0.08), int(h * 0.11), int(w * 0.84), int(h * 0.44))
        price_cx, price_cy, price_r = int(w * 0.74), int(h * 0.52), int(w * 0.185)
        head_y = int(h * 0.66)
    else:
        disc_cx, disc_cy, disc_r = int(w * 0.80), int(h * 0.18), int(w * 0.50)
        prod = Zone(int(w * 0.10), int(h * 0.12), int(w * 0.66), int(h * 0.54))
        price_cx, price_cy, price_r = int(w * 0.82), int(h * 0.60), int(w * 0.155)
        head_y = int(h * 0.68)

    # Colour disc with shadow + gradient.
    ds = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ds).ellipse((disc_cx - disc_r, disc_cy - disc_r + int(disc_r * 0.05),
                                disc_cx + disc_r, disc_cy + disc_r + int(disc_r * 0.05)),
                               fill=(*_darken(accent, 0.4), 55))
    canvas.alpha_composite(ds.filter(ImageFilter.GaussianBlur(radius=max(12, disc_r // 14))))
    _fill_gradient_shape(canvas, _circle_points(disc_cx, disc_cy, disc_r),
                         top=_lighten(accent, 0.20), bottom=_darken(accent, 0.16))
    _draw_spotlight(canvas, disc_cx, disc_cy - int(disc_r * 0.3), int(disc_r * 0.7), white, 50, falloff=1.7)
    draw = ImageDraw.Draw(canvas)

    sw, sh_h = int(prod.w * 0.46), int(prod.h * 0.06)
    _draw_soft_shadow(canvas, prod.cx - sw // 2, int(prod.cy + prod.h * 0.30), sw, sh_h,
                      blur=max(14, prod.w // 15), intensity=70)
    _draw_product_or_name(canvas, draw, spec, prod, ink)

    _draw_brand_lockup(canvas, margin, int(h * 0.05), int(h * (0.06 if tall else 0.085)), ink, sub_color=muted, halo=False)
    _draw_context_tags(canvas, spec, margin, int(h * (0.135 if tall else 0.17)), int(w * 0.05))

    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        _draw_discount_burst(canvas, discount, int(price_cx - price_r * 0.9), int(price_cy - price_r * 0.95), int(price_r * 0.5))
    _draw_price_disc(canvas, spec, price_cx, price_cy, price_r, ink, white, ring=accent,
                     gradient=(_lighten(ink, 0.16), _darken(ink, 0.1)))
    _draw_validity_tag(canvas, spec, price_cx, int(price_cy + price_r * 1.16), int(w * 0.05), accent, white)

    # Kicker + accent rule + oversized headline + claim.
    kh = int(h * 0.02)
    _draw_kicker(draw, margin, head_y, (spec.category or "Aktion"), kh, accent)
    bar_y = head_y + int(kh * 1.8)
    draw.rounded_rectangle((margin, bar_y, margin + int(w * 0.11), bar_y + max(4, int(h * 0.009))), radius=h // 220, fill=accent)
    _draw_headline_block(draw, spec, Zone(margin, bar_y + int(h * 0.028), int(w * 0.58), int(h * 0.14)), ink, align="left", claim_color=muted)

    foot = f"{STORE_NAME}   ·   {INSTAGRAM}"
    ff = _load_font(FONT_PATH_REGULAR, int(h * 0.016))
    fb = draw.textbbox((0, 0), foot, font=ff)
    draw.text(((w - (fb[2] - fb[0])) // 2 - fb[0], h - int(h * 0.05) - fb[1]), foot, fill=muted, font=ff)


def _layout_colorblock(canvas: Image.Image, spec: PromotionSpec, fmt: FormatType):
    """Swiss/Bauhaus style: a bold colour block holds the product, the rest is
    white with strong typography. Geometric and graphic."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    tall = h / w > 1.12
    accent = _product_accent(spec)
    ink = (24, 24, 26)
    white = (255, 255, 255)
    muted = (120, 120, 126)
    draw.rectangle((0, 0, w, h), fill=white)

    if tall:
        # Top colour band holds the product; text column below.
        band_h = int(h * 0.52)
        draw.rectangle((0, 0, w, band_h), fill=accent)
        prod = Zone(int(w * 0.10), int(h * 0.06), int(w * 0.80), int(band_h - h * 0.12))
        col_x, col_w = int(w * 0.08), int(w * 0.84)
        head_y = int(band_h + h * 0.05)
        lock_color = white
        lock_y = int(h * 0.05)
    else:
        # Left colour block holds the product; text column on the right.
        band_w = int(w * 0.47)
        draw.rectangle((0, 0, band_w, h), fill=accent)
        prod = Zone(int(w * 0.02), int(h * 0.16), int(band_w - w * 0.04), int(h * 0.62))
        col_x, col_w = int(w * 0.52), int(w * 0.40)
        head_y = int(h * 0.34)
        lock_color = ink
        lock_y = int(h * 0.08)

    # Product on the colour block (with a soft shadow for depth).
    sw, sh_h = int(prod.w * 0.5), int(prod.h * 0.05)
    _draw_soft_shadow(canvas, prod.cx - sw // 2, int(prod.cy + prod.h * 0.32), sw, sh_h,
                      blur=max(14, prod.w // 15), intensity=60)
    _draw_product_or_name(canvas, draw, spec, prod, white)

    # Brand lockup.
    _draw_brand_lockup(canvas, col_x, lock_y, int(h * (0.058 if tall else 0.072)), lock_color,
                       sub_color=_mix(lock_color, accent, 0.0), halo=False)

    # Kicker + big headline.
    kh = int(h * 0.02)
    _draw_kicker(draw, col_x, head_y, (spec.category or "Angebot"), kh, accent)
    name_font, name_lines = _fit_wrapped(draw, spec.product.upper(), FONT_PATH_EXTRABOLD,
                                         col_w, int(h * 0.22), int(h * 0.085), int(h * 0.04),
                                         max_lines=2, line_spacing=1.0)
    ny = _draw_wrapped(draw, name_lines, col_x, col_w, head_y + int(kh * 1.9), name_font, ink, align="left", line_spacing=1.0)
    draw.rectangle((col_x, ny + int(h * 0.01), col_x + int(w * 0.10), ny + int(h * 0.01) + max(4, int(h * 0.01))), fill=accent)
    ny += int(h * 0.045)

    if spec.claim:
        cf = _load_font(FONT_PATH_REGULAR, int(h * 0.026))
        for line in _wrap_text(draw, spec.claim, cf, col_w, 2):
            b = draw.textbbox((0, 0), line, font=cf)
            draw.text((col_x - b[0], ny - b[1]), line, fill=muted, font=cf)
            ny += int((b[3] - b[1]) * 1.35)
    ny += int(h * 0.02)

    # Price block: statt + big price + validity/discount.
    if spec.old_price:
        of = _load_font(FONT_PATH_REGULAR, int(h * 0.026))
        ot = f"statt {spec.old_price}"
        ob = draw.textbbox((0, 0), ot, font=of)
        draw.text((col_x - ob[0], ny - ob[1]), ot, fill=muted, font=of)
        draw.line((col_x, ny + (ob[3] - ob[1]) * 0.55, col_x + (ob[2] - ob[0]), ny + (ob[3] - ob[1]) * 0.55), fill=muted, width=max(2, h // 600))
        ny += int(h * 0.042)
    pf = _fit_font_width(draw, spec.price, FONT_PATH_EXTRABOLD, col_w, int(h * 0.085), int(h * 0.05))
    pb = draw.textbbox((0, 0), spec.price, font=pf)
    draw.text((col_x - pb[0], ny - pb[1]), spec.price, fill=accent, font=pf)
    ny += int((pb[3] - pb[1]) + h * 0.02)

    meta = spec.validity.upper()
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        meta = f"{meta}   ·   −{discount}%"
    mf = _load_font(FONT_PATH_SEMIBOLD, int(h * 0.02))
    mb = draw.textbbox((0, 0), meta, font=mf)
    draw.text((col_x - mb[0], ny - mb[1]), meta, fill=ink, font=mf)

    # Context badge bottom of text column.
    ctx = _context_tags(spec)
    if ctx:
        _draw_kicker(draw, col_x, int(h * 0.9), ctx[0][0], int(h * 0.016), accent)


@dataclass
class StyleConfig:
    primary: tuple[int, int, int]
    accent: tuple[int, int, int]
    bg_light: float
    bg_dark: float
    vignette: int
    star_scale: float
    halo_alpha: int
    spotlight_alpha: int
    force_region: bool


def _enum_val(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _build_style_config(spec: PromotionSpec, primary, accent, style: str = "edeka") -> StyleConfig:
    """Translate Tonalität (mood/colour) and Kreativniveau (intensity) into
    concrete drawing parameters."""
    tone = _enum_val(spec.tone)
    level = _enum_val(spec.differentiation_level)
    edeka = style == "edeka"

    bg_light, bg_dark, vignette = 0.10, 0.35, 120
    star_scale, halo, spot = 1.0, 120, 165
    force_region = False

    # --- Tonalität: mood (colour tweaks only for EDEKA Style; Kreativ already
    #     uses a distinct colour theme per tone) ---
    if tone == "premium":          # elegant, deep
        if edeka:
            primary = _darken(primary, 0.18)
            accent = _mix(accent, (255, 176, 32), 0.28)
        bg_light, bg_dark, vignette = 0.04, 0.52, 185
        star_scale *= 0.95
    elif tone == "atrevido":       # Mutig: louder, bigger, brighter
        if edeka:
            primary = _lighten(primary, 0.05)
        star_scale *= 1.12
        halo += 45
        spot += 25
    elif tone == "local":          # warm + always show the region badge
        if edeka:
            accent = _mix(accent, (255, 168, 64), 0.22)
        force_region = True
        bg_dark = 0.42
    # "fresco" keeps the defaults

    # --- Kreativniveau: how much visual punch ---
    if level == "bajo":            # Dezent: clean, restrained
        star_scale *= 0.90
        halo = int(halo * 0.5)
        spot = int(spot * 0.7)
        vignette = int(vignette * 0.55)
        bg_light += 0.04
    elif level == "alto":          # Auffällig: maximum impact
        star_scale *= 1.13
        halo = int(halo * 1.45)
        spot = int(spot * 1.2)

    return StyleConfig(primary, accent, bg_light, bg_dark, vignette,
                       round(star_scale, 3), halo, spot, force_region)


def _layout_post(canvas: Image.Image, spec: PromotionSpec, cfg: StyleConfig):
    w, h = canvas.size
    margin = int(w * 0.05)
    white = (255, 255, 255)
    primary, accent = cfg.primary, cfg.accent
    _paint_background(canvas, cfg)
    draw = ImageDraw.Draw(canvas)

    # Soft warm halo behind the star (intensity from Kreativniveau).
    star_cx, star_cy, star_r = int(w * 0.74), int(h * 0.46), int(w * 0.24 * cfg.star_scale)
    _draw_spotlight(canvas, star_cx, star_cy, int(star_r * 1.7), _lighten(accent, 0.45), cfg.halo_alpha)

    _draw_brand_lockup(canvas, margin, int(h * 0.05), int(h * 0.10), accent)
    _draw_angebot_badge(canvas, int(w * 0.83), int(h * 0.085), int(h * 0.058), accent, primary)

    # Product hero on the left, lifted by a warm spotlight.
    _draw_spotlight(canvas, int(w * 0.31), int(h * 0.43), int(w * 0.36), _lighten(accent, 0.5), cfg.spotlight_alpha)
    _draw_product_or_name(canvas, draw, spec, Zone(int(w * 0.02), int(h * 0.20), int(w * 0.56), int(h * 0.44)), white)

    _draw_context_tags(canvas, spec, margin, int(h * 0.205), int(w * 0.052), force_region=cfg.force_region)

    _draw_price_star(canvas, spec, star_cx, star_cy, star_r, primary, accent)
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        _draw_discount_burst(canvas, discount, int(star_cx - star_r * 0.78), int(star_cy - star_r * 0.88), int(star_r * 0.46))
    _draw_validity_tag(canvas, spec, star_cx, int(star_cy + star_r * 1.0), int(w * 0.052), accent, primary)

    _draw_headline_block(draw, spec, Zone(margin, int(h * 0.70), int(w * 0.62), int(h * 0.14)), white, align="left", claim_color=CLAIM_LIGHT)
    _draw_footer_text(canvas, accent, margin)


def _layout_story(canvas: Image.Image, spec: PromotionSpec, cfg: StyleConfig):
    w, h = canvas.size
    margin = int(w * 0.06)
    white = (255, 255, 255)
    primary, accent = cfg.primary, cfg.accent
    _paint_background(canvas, cfg)
    draw = ImageDraw.Draw(canvas)

    star_cx, star_cy, star_r = int(w * 0.70), int(h * 0.55), int(w * 0.27 * cfg.star_scale)
    _draw_spotlight(canvas, star_cx, star_cy, int(star_r * 1.8), _lighten(accent, 0.45), cfg.halo_alpha)

    _draw_brand_lockup(canvas, margin, int(h * 0.04), int(h * 0.072), accent)
    _draw_angebot_badge(canvas, int(w * 0.78), int(h * 0.066), int(h * 0.04), accent, primary)

    _draw_spotlight(canvas, int(w * 0.5), int(h * 0.31), int(w * 0.52), _lighten(accent, 0.5), cfg.spotlight_alpha)
    _draw_product_or_name(canvas, draw, spec, Zone(margin, int(h * 0.13), w - margin * 2, int(h * 0.32)), white)
    _draw_context_tags(canvas, spec, margin, int(h * 0.12), int(w * 0.06), force_region=cfg.force_region)

    _draw_price_star(canvas, spec, star_cx, star_cy, star_r, primary, accent)
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        _draw_discount_burst(canvas, discount, int(star_cx - star_r * 0.80), int(star_cy - star_r * 0.86), int(star_r * 0.42))

    _draw_headline_block(draw, spec, Zone(margin, int(h * 0.70), int(w * 0.60), int(h * 0.13)), white, align="left", claim_color=CLAIM_LIGHT)
    _draw_validity_tag(canvas, spec, int(w * 0.30), int(h * 0.85), int(w * 0.058), accent, primary)
    _draw_footer_text(canvas, accent, margin)


def _layout_poster(canvas: Image.Image, spec: PromotionSpec, cfg: StyleConfig):
    w, h = canvas.size
    margin = int(w * 0.06)
    white = (255, 255, 255)
    primary, accent = cfg.primary, cfg.accent
    _paint_background(canvas, cfg)
    draw = ImageDraw.Draw(canvas)

    star_cx, star_cy, star_r = int(w * 0.69), int(h * 0.585), int(w * 0.27 * cfg.star_scale)
    _draw_spotlight(canvas, star_cx, star_cy, int(star_r * 1.9), _lighten(accent, 0.45), cfg.halo_alpha)

    _draw_brand_lockup(canvas, margin, int(h * 0.035), int(h * 0.060), accent)
    _draw_angebot_badge(canvas, int(w * 0.80), int(h * 0.052), int(h * 0.034), accent, primary)

    _draw_spotlight(canvas, int(w * 0.5), int(h * 0.32), int(w * 0.46), _lighten(accent, 0.5), cfg.spotlight_alpha)
    _draw_product_or_name(canvas, draw, spec, Zone(margin, int(h * 0.11), w - margin * 2, int(h * 0.40)), white)
    _draw_context_tags(canvas, spec, margin, int(h * 0.10), int(w * 0.05), force_region=cfg.force_region)

    _draw_price_star(canvas, spec, star_cx, star_cy, star_r, primary, accent)
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        _draw_discount_burst(canvas, discount, int(star_cx - star_r * 0.80), int(star_cy - star_r * 0.86), int(star_r * 0.44))

    _draw_headline_block(draw, spec, Zone(margin, int(h * 0.70), int(w * 0.52), int(h * 0.15)), white, align="left", claim_color=CLAIM_LIGHT)
    _draw_validity_tag(canvas, spec, int(w * 0.28), int(h * 0.87), int(w * 0.05), accent, primary)
    _draw_footer_text(canvas, accent, margin)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compose_promotion(
    spec: PromotionSpec,
    direction: CreativeDirection,
    format_type: FormatType,
    output_path: Path,
    scale: float = 1.0,
) -> Path:
    fmt = EXPORT_FORMATS[format_type]
    # `scale` < 1 renders a smaller canvas for fast previews; the layout is
    # fully proportional so the result is identical, just lower resolution.
    cw = max(1, round(fmt.width * scale))
    ch = max(1, round(fmt.height * scale))
    canvas = Image.new("RGBA", (cw, ch), (255, 255, 255, 255))

    style = (getattr(spec, "style", None) or "edeka").lower()
    if style == "luxe":
        _layout_luxe(canvas, spec, format_type)
    elif style == "editorial":
        _layout_editorial(canvas, spec, format_type)
    elif style == "colorblock":
        _layout_colorblock(canvas, spec, format_type)
    else:
        # EDEKA Style: bold Knaller layout, fixed brand colours.
        primary = _hex_to_rgb(BRAND_BLUE)
        accent = _hex_to_rgb(BRAND_YELLOW)
        cfg = _build_style_config(spec, primary, accent, "edeka")
        if format_type == FormatType.POST:
            _layout_post(canvas, spec, cfg)
        elif format_type == FormatType.STORY:
            _layout_story(canvas, spec, cfg)
        else:
            _layout_poster(canvas, spec, cfg)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(str(output_path), quality=96, optimize=True)
    return output_path
