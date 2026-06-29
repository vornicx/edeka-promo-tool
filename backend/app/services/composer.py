from __future__ import annotations

import colorsys
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from app.assets.brand import (
    BRAND_ANTHRACITE,
    BRAND_BLUE,
    BRAND_YELLOW,
    FONT_PATH_BOLD,
    FONT_PATH_DISPLAY,
    FONT_PATH_DISPLAY_COMPRESSED,
    FONT_PATH_DISPLAY_LIGHT,
    FONT_PATH_DISPLAY_MED,
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
BANNER_PATH = Path(__file__).resolve().parent.parent / "assets" / "banner.png"
INSTAGRAM_URL = "https://www.instagram.com/waschbaer_edeka/"
INSTAGRAM_HANDLE = "@waschbaer_edeka"
QR_PATH = Path(__file__).resolve().parent.parent / "assets" / "instagram_waschbaer_qr_square.png"
STORE_ADDRESS = "Wolfsangerstr. 100 · 34125 Kassel · Mo–Sa 7–21 Uhr"

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
    "pointed_peppers": ["spitzpaprika", "bio spitzpaprika", "rote paprika", "rot paprika", "pointed pepper"],
    "peppers": ["pimiento", "pimientos", "paprika", "bell pepper", "peppers"],
    "cheese_slices": ["milram", "kaesescheiben", "kasescheiben", "reibekaese", "reibekase", "gouda", "scheibenkaese", "scheibenkase", "kaese", "kase", "cheese"],
    "soft_cheese": ["cambozola", "rougette", "allgaeuer", "allgauer", "rahmtorte", "bedientheke", "weichkaese", "weichkase"],
    "juice_bottle": ["saft", "nektar", "juice", "apfelsaft", "orangensaft"],
    "milk_drink": ["muellermilch", "mullermilch", "milchdrink", "milch mix", "erdbeer-geschmack"],
    "icecream_bars": ["magnum", "multipack", "eis am stiel", "stieleis", "ice cream bars"],
    "ice_cream_tub": ["moevenpick", "movenpick", "eisbecher", "eis", "speiseeis", "ice cream"],
    "pizza": ["wagner", "pizza", "pizzies", "flammkuchen", "steinofen"],
    "pesto_sauce": ["barilla pesto", "pesto", "pastasauce", "sauce"],
    "pasta": ["barilla pasta", "pasta", "nudeln", "spaghetti", "penne"],
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
    want_words = len(text.split())
    best: tuple[ImageFont.ImageFont, list[str]] | None = None
    while size >= min_size:
        font = _load_font(font_path, size)
        lines = _wrap_text(draw, text, font, max_width, max_lines)
        widest = max((_text_size(draw, line, font)[0] for line in lines), default=0)
        line_h = _text_size(draw, "Ág", font)[1]
        total_h = int(line_h * line_spacing * len(lines))
        # Must fit the box AND keep every word (no truncation by max_lines).
        got_words = sum(len(line.split()) for line in lines)
        if widest <= max_width and total_h <= max_height and got_words >= want_words:
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


def _draw_wrapped_shadow(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    zone_x: int,
    zone_w: int,
    y: int,
    font: ImageFont.ImageFont,
    fill,
    align: str = "left",
    line_spacing: float = 1.12,
    shadow=(0, 24, 54, 170),
    shadow_offset: tuple[int, int] = (0, 3),
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
        draw.text((lx + shadow_offset[0], y + shadow_offset[1]), line, fill=shadow, font=font)
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


def _copy_clean(value: str | None) -> str:
    text = (value or "").strip()
    replacements = {
        "Fussball": "Fußball",
        "fussball": "Fußball",
        "Getraenke": "Getränke",
        "getraenke": "Getränke",
        "Suesse": "Süße",
        "suesse": "süße",
        "Suess": "Süß",
        "suess": "süß",
        "Schokoladenverkostung": "Schokoladen-Verkostung",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text).strip()


def _event_copy_kind(spec: PromotionSpec) -> str:
    text = _normalize(f"{spec.product} {spec.claim or ''} {spec.event_description or ''} {spec.price or ''}")
    if any(word in text for word in ["wm", "world cup", "weltmeisterschaft", "fussball", "public viewing"]):
        return "football"
    if any(word in text for word in ["chocolate", "schoko", "schokolade", "praline", "kakao"]):
        return "chocolate"
    if any(word in text for word in ["wein", "verkostung", "tasting"]):
        return "tasting"
    if any(word in text for word in ["sommer", "grill", "garten"]):
        return "summer"
    return "event"


def _display_title(spec: PromotionSpec) -> str:
    raw = _copy_clean(spec.product)
    kind = _event_copy_kind(spec) if _is_event(spec) else ""
    if kind == "football" and any(word in _normalize(raw) for word in ["wm", "world cup", "weltmeisterschaft"]):
        return "WM-Party"
    if kind == "football":
        return "Fußballabend im Markt"
    if kind == "chocolate":
        return "Schokoladen-Verkostung"
    if kind == "tasting" and "verkostung" not in _normalize(raw):
        return f"{raw} Verkostung".strip()
    return raw


def _event_kicker(spec: PromotionSpec) -> str:
    kind = _event_copy_kind(spec)
    if kind == "football":
        return "Live im Markt"
    if kind == "chocolate":
        return "Genussmoment"
    if kind == "tasting":
        return "Verkostung"
    if kind == "summer":
        return "Sommer im Markt"
    return "Aktion im Markt"


def _event_description_copy(spec: PromotionSpec) -> str:
    kind = _event_copy_kind(spec)
    if kind == "football":
        return "Gemeinsam schauen, anfeuern und genießen. Mit Snacks und Getränken vor Ort."
    if kind == "chocolate":
        return "Feine Schokoladen probieren, vergleichen und neue Lieblingssorten entdecken."
    if kind == "tasting":
        return "Ausgewählte Spezialitäten probieren und persönlich beraten lassen."
    if kind == "summer":
        return "Sommerliche Aktionen, gute Angebote und Begegnung direkt im Markt."
    raw = _copy_clean(spec.claim or spec.event_description or spec.origin or "")
    if len(raw) <= 120:
        return raw
    shortened = raw[:117].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{shortened}."


def _short_event_info(value: str | None) -> str:
    text = _copy_clean(value).upper()
    if not text:
        return ""
    weekday_map = {
        "MONTAG": "MO",
        "DIENSTAG": "DI",
        "MITTWOCH": "MI",
        "DONNERSTAG": "DO",
        "FREITAG": "FR",
        "SAMSTAG": "SA",
        "SONNTAG": "SO",
    }
    for full, short in weekday_map.items():
        text = re.sub(rf"\b{full}\b", short, text)
    text = text.replace("EDEKA MÜHLENBEIN KASSEL", "KASSEL")
    text = text.replace("EDEKA MÜHLENBEIN", "IM MARKT")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 28:
        text = text[:26].rsplit(" ", 1)[0].rstrip(".,;:") or text[:26].rstrip(".,;:")
    return text


def _event_date_parts(value: str | None) -> tuple[str, str]:
    text = _short_event_info(value)
    if "," in text:
        day, time = text.split(",", 1)
        return day.strip(), time.strip()
    match = re.match(r"^(MO|DI|MI|DO|FR|SA|SO)\b\s*(.*)$", text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "TERMIN", text or "VOR ORT"


def _event_detail_cards(spec: PromotionSpec, day: str, time_value: str) -> list[tuple[str, str]]:
    kind = _event_copy_kind(spec)
    time_label = day if day and day != "TERMIN" else "TERMIN"
    time_text = time_value or "VOR ORT"
    if kind == "football":
        return [
            (time_label, time_text),
            ("PUBLIC", "VIEWING"),
            ("SNACKS &", "GETRÄNKE"),
            ("EINTRITT", "FREI"),
        ]
    if kind == "chocolate":
        return [
            (time_label, time_text),
            ("PROBIEREN", "GENIESSEN"),
            ("FEINE", "SCHOKOLADEN"),
            ("DIREKT", "IM MARKT"),
        ]
    if kind == "tasting":
        return [
            (time_label, time_text),
            ("PROBIEREN", "ENTDECKEN"),
            ("DIREKT", "IM MARKT"),
            ("BERATUNG", "VOR ORT"),
        ]
    if kind == "summer":
        return [
            (time_label, time_text),
            ("AKTIONEN", "IM MARKT"),
            ("GENIESSEN", "VOR ORT"),
            ("FÜR ALLE", "VORBEIKOMMEN"),
        ]
    event_note = _short_event_info(spec.price)
    return [
        (time_label, time_text),
        ("AKTION", "IM MARKT"),
        ("INFO", event_note or "VOR ORT"),
        ("EDEKA", "MÜHLENBEIN"),
    ]


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
    alpha = image.getchannel("A") if image.mode == "RGBA" else None
    bbox = alpha.getbbox() if alpha else image.getbbox()
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
    product = product.resize(new_size, Image.Resampling.LANCZOS)
    # When upscaling for high-res output, a gentle unsharp keeps the product crisp.
    if scale > 1.12:
        rgb = product.convert("RGB").filter(ImageFilter.UnsharpMask(radius=2.4, percent=90, threshold=2))
        rgb.putalpha(product.getchannel("A"))
        product = rgb
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


def _cover_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    source = image.convert("RGBA")
    scale = max(target_w / source.width, target_h / source.height)
    resized = source.resize((max(1, int(source.width * scale)), max(1, int(source.height * scale))), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


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


def _is_event(spec: PromotionSpec) -> bool:
    return getattr(spec, "campaign_kind", None) and spec.campaign_kind.value == "event"


def _offer_value(spec: PromotionSpec) -> str:
    value = (spec.price or "").strip()
    if value:
        return value
    return "AKTION" if _is_event(spec) else "0 €"


def _offer_label(spec: PromotionSpec) -> str:
    return "MARKTAKTION" if _is_event(spec) else "ANGEBOT"


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
        small = max(10, int(size * 0.48))
        cents_font = _load_font(FONT_PATH_EXTRABOLD, small)
        cur_font = _load_font(FONT_PATH_BOLD, max(10, int(size * 0.43)))
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

    inner = int(radius * 0.72)
    # "statt" struck-through old price at the upper area.
    top_cursor = cy - int(inner * 0.78)
    if spec.old_price and not _is_event(spec):
        old_text = f"statt {spec.old_price}"
        of = _fit_font_width(draw, old_text, FONT_PATH_BOLD, int(inner * 1.5), int(radius * 0.16), int(radius * 0.09))
        ob = draw.textbbox((0, 0), old_text, font=of)
        ow, oh = ob[2] - ob[0], ob[3] - ob[1]
        ox = cx - ow // 2
        draw.text((ox - ob[0], top_cursor - ob[1]), old_text, fill=_darken(primary, 0.15), font=of)
        draw.line((ox, top_cursor + oh * 0.5, ox + ow, top_cursor + oh * 0.5), fill=RED, width=max(3, radius // 40))
        price_cy = cy + int(radius * 0.07)
        price_h = int(radius * 0.70)
    else:
        price_cy = cy
        price_h = int(radius * 0.90)

    _draw_price_value(draw, cx, price_cy, int(inner * 1.9), price_h, _offer_value(spec), primary)


def _avg_region(canvas: Image.Image, x: int, y: int, s: int) -> tuple[int, int, int]:
    box = canvas.crop((x, y, x + s, y + s)).convert("RGB")
    px = list(box.getdata())
    n = len(px)
    return (sum(p[0] for p in px) // n, sum(p[1] for p in px) // n, sum(p[2] for p in px) // n)


def _luminance(rgb: tuple[int, int, int]) -> float:
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def _qr_palette(bg: tuple[int, int, int], wordmark: tuple[int, int, int]) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    """Return (module, accent, panel) colours for a design-matched QR block.

    QR scanners need high contrast, so the modules stay dark on a light panel;
    the surrounding frame and handle borrow the current design accent.
    """
    if _luminance(bg) < 140:
        module = _darken(bg, 0.38)
        accent = wordmark
        panel = (255, 255, 255)
    else:
        module = wordmark if _luminance(wordmark) < 135 else _hex_to_rgb(BRAND_BLUE)
        accent = module
        panel = _lighten(bg, 0.86)
    if _luminance(module) > 150:
        module = _hex_to_rgb(BRAND_BLUE)
    return module, accent, panel


def _tint_qr(qr: Image.Image, module: tuple[int, int, int], panel: tuple[int, int, int]) -> Image.Image:
    """Recolour black QR modules while preserving a light quiet zone."""
    qr = qr.convert("L")
    out = Image.new("RGBA", qr.size, (*panel, 255))
    pixels = out.load()
    source = qr.load()
    for y in range(qr.height):
        for x in range(qr.width):
            if source[x, y] < 128:
                pixels[x, y] = (*module, 255)
    return out


def _draw_footer_banner(canvas: Image.Image, spec: PromotionSpec) -> int:
    """Footer rebuilt to match each design: it blends with the canvas colour at
    the bottom and shows EDEKA Mühlenbein + address + the Instagram QR in the
    design's own tones, instead of pasting the dark banner image."""
    w, h = canvas.size
    band_h = int(h * 0.12)
    top = h - band_h

    # Adopt the design's bottom colour so the footer blends in. If the two
    # bottom corners differ a lot (e.g. Color Block), fall back to a light bar.
    bl = _avg_region(canvas, 4, h - 18, 14)
    br = _avg_region(canvas, w - 18, h - 18, 14)
    dist = sum(abs(bl[i] - br[i]) for i in range(3))
    bg = _mix(bl, br, 0.5) if dist < 60 else (249, 248, 246)
    lum = 0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]
    ink = (245, 243, 238) if lum < 140 else (32, 30, 30)
    muted = _mix(ink, bg, 0.42)
    wordmark = _hex_to_rgb(BRAND_YELLOW) if lum < 140 else _hex_to_rgb(BRAND_BLUE)
    qr_module, qr_accent, qr_panel = _qr_palette(bg, wordmark)

    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, top, w, h), fill=bg)
    draw.rectangle((0, top, w, top + max(2, h // 520)), fill=_mix(ink, bg, 0.72))

    margin = int(w * 0.05)
    cy = top + band_h // 2
    # No mascot here — the brand lockup at the top already shows it (avoid
    # duplicating the Waschbär). The footer is the contact strip.
    tx = margin

    # Instagram QR at the far right first, so the text block knows its limit.
    # The QR asset is generated for INSTAGRAM_URL; the visible handle is drawn
    # separately so it remains readable after resizing.
    right_limit = w - margin
    if QR_PATH.exists():
        qr = Image.open(QR_PATH).convert("RGBA")
        qh = int(band_h * 0.55)
        qr = qr.resize((qh, qh), Image.Resampling.LANCZOS)
        qr = _tint_qr(qr, qr_module, qr_panel)
        handle_font = _fit_font_width(draw, INSTAGRAM_HANDLE, FONT_PATH_BOLD, int(band_h * 1.35), int(band_h * 0.13), int(band_h * 0.075))
        hb = draw.textbbox((0, 0), INSTAGRAM_HANDLE, font=handle_font)
        handle_w, handle_h = hb[2] - hb[0], hb[3] - hb[1]
        cp = max(4, int(band_h * 0.045))
        gap = max(3, int(band_h * 0.035))
        box_w = max(qr.width + cp * 2, handle_w + cp * 2)
        box_h = qr.height + handle_h + gap + cp * 2
        qx = w - margin - box_w
        qy = top + (band_h - box_h) // 2
        draw.rounded_rectangle(
            (qx, qy, qx + box_w, qy + box_h),
            radius=max(6, int(band_h * 0.08)),
            fill=qr_panel,
            outline=qr_accent,
            width=max(1, int(band_h * 0.012)),
        )
        qr_x = qx + (box_w - qr.width) // 2
        qr_y = qy + cp
        canvas.alpha_composite(qr, (qr_x, qr_y))
        handle_x = qx + (box_w - handle_w) // 2
        handle_y = qr_y + qr.height + gap
        draw.text((handle_x - hb[0], handle_y - hb[1]), INSTAGRAM_HANDLE, fill=qr_accent, font=handle_font)
        right_limit = qx - int(band_h * 0.16)

    # EDEKA Mühlenbein + address, fitted to the remaining width (never overflow).
    text_w = max(int(w * 0.2), right_limit - tx)
    f1 = _fit_font_width(draw, "EDEKA Mühlenbein", FONT_PATH_EXTRABOLD, text_w, int(band_h * 0.30), int(band_h * 0.15))
    eb = draw.textbbox((0, 0), "EDEKA", font=f1)
    f2 = _fit_font_width(draw, STORE_ADDRESS, FONT_PATH_SEMIBOLD, text_w, int(band_h * 0.17), int(band_h * 0.085))
    ab = draw.textbbox((0, 0), STORE_ADDRESS, font=f2)
    gap = int(band_h * 0.08)
    block_h = (eb[3] - eb[1]) + gap + (ab[3] - ab[1])
    line1_y = cy - block_h // 2
    draw.text((tx - eb[0], line1_y - eb[1]), "EDEKA", fill=wordmark, font=f1)
    mx = tx + (eb[2] - eb[0]) + int(f1.size * 0.22)
    mb = draw.textbbox((0, 0), "Mühlenbein", font=f1)
    draw.text((mx - mb[0], line1_y - mb[1]), "Mühlenbein", fill=ink, font=f1)
    draw.text((tx - ab[0], line1_y + (eb[3] - eb[1]) + gap - ab[1]), STORE_ADDRESS, fill=muted, font=f2)
    return band_h


def _contrast_text(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return (26, 26, 28) if lum > 150 else (255, 255, 255)


def _draw_price_card(canvas: Image.Image, spec: PromotionSpec, zone: Zone, fill: tuple[int, int, int]):
    """High-contrast rounded price card (rectangular, not a seal) with a big,
    clearly readable price — the clarity of the EDEKA card, recoloured."""
    draw = ImageDraw.Draw(canvas)
    x, y, w, h = zone.x, zone.y, zone.w, zone.h
    text = _contrast_text(fill)
    sub = _mix(text, fill, 0.3)
    pill = _darken(fill, 0.42)
    pill_text = _contrast_text(pill)
    radius = min(w, h) // 7

    # Soft drop shadow.
    pad = max(16, w // 26)
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle((pad, pad, w + pad, h + pad), radius=radius + 8, fill=(0, 0, 0, 95))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius=pad // 2)), (x - pad, y - pad + pad // 3))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill)

    px, py = int(w * 0.075), int(h * 0.09)
    ix, iy, iw = x + px, y + py, w - px * 2
    bottom = y + h - py

    # Validity pill, bottom-left.
    vt = spec.validity.upper()
    pill_h = int(h * 0.15)
    vf = _fit_font_height(draw, vt, FONT_PATH_BOLD, int(pill_h * 0.52), int(pill_h * 0.6), int(pill_h * 0.34))
    vb = draw.textbbox((0, 0), vt, font=vf)
    vw = vb[2] - vb[0]
    ppx = int(pill_h * 0.5)
    pill_w = min(iw, vw + ppx * 2)
    pill_y = bottom - pill_h
    draw.rounded_rectangle((ix, pill_y, ix + pill_w, pill_y + pill_h), radius=pill_h // 2, fill=pill)
    draw.text((ix + (pill_w - vw) // 2 - vb[0], pill_y + (pill_h - (vb[3] - vb[1])) // 2 - vb[1]), vt, fill=pill_text, font=vf)

    # "ANGEBOT/EVENT" label (left) + struck old price (right), top band.
    lh = int(h * 0.13)
    label = _offer_label(spec)
    lf = _fit_font_height(draw, label, FONT_PATH_EXTRABOLD, lh, int(lh * 1.1), int(lh * 0.6))
    lb = draw.textbbox((0, 0), label, font=lf)
    draw.text((ix - lb[0], iy - lb[1]), label, fill=text, font=lf)
    label_bottom = iy + (lb[3] - lb[1])
    if spec.old_price and not _is_event(spec):
        ot = f"statt {spec.old_price}"
        of = _fit_font_height(draw, ot, FONT_PATH_BOLD, int(lh * 0.74), int(lh), int(lh * 0.45))
        ob = draw.textbbox((0, 0), ot, font=of)
        ow, oh = ob[2] - ob[0], ob[3] - ob[1]
        ox = x + w - px - ow
        oy = label_bottom - oh
        draw.text((ox - ob[0], oy - ob[1]), ot, fill=sub, font=of)
        draw.line((ox, oy + oh * 0.55, ox + ow, oy + oh * 0.55), fill=RED, width=max(2, h // 80))

    # Big, dominant price.
    pt = label_bottom + int(h * 0.025)
    pb = pill_y - int(h * 0.025)
    band = max(int(h * 0.24), pb - pt)
    value = _offer_value(spec)
    pf = _fit_font_width(draw, value, FONT_PATH_EXTRABOLD, iw, int(band * 1.18), int(band * 0.52))
    pf = _fit_font_height(draw, value, FONT_PATH_EXTRABOLD, band, pf.size, int(band * 0.48))
    bbox = draw.textbbox((0, 0), value, font=pf)
    pw = bbox[2] - bbox[0]
    draw.text((ix + (iw - pw) // 2 - bbox[0], pt + (band - (bbox[3] - bbox[1])) // 2 - bbox[1]), value, fill=text, font=pf)


def _draw_discount_burst(canvas: Image.Image, percent: int, cx: int, cy: int, radius: int):
    """Small red explosion badge for the discount percentage."""
    _draw_discount_burst_colored(canvas, percent, cx, cy, radius, RED, (255, 255, 255))


def _draw_discount_burst_colored(
    canvas: Image.Image,
    percent: int,
    cx: int,
    cy: int,
    radius: int,
    fill: tuple[int, int, int],
    text_color: tuple[int, int, int],
):
    """Small explosion badge for the discount percentage."""
    white = (255, 255, 255)
    _aa_polygon(canvas, _star_points(cx, cy, radius, radius * 0.72, 12, rot=0.2), fill=white)
    _aa_polygon(canvas, _star_points(cx, cy, radius * 0.88, radius * 0.62, 12, rot=0.2), fill=fill)
    draw = ImageDraw.Draw(canvas)
    text = f"-{percent}%"
    font = _fit_font_width(draw, text, FONT_PATH_EXTRABOLD, int(radius * 1.25), int(radius * 0.8), int(radius * 0.4))
    b = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (b[2] - b[0]) / 2 - b[0], cy - (b[3] - b[1]) / 2 - b[1]), text, fill=text_color, font=font)


def _draw_tag(
    canvas: Image.Image,
    text: str,
    cx: int,
    cy: int,
    height: int,
    bg: tuple[int, int, int],
    fg: tuple[int, int, int],
    angle: float = 0.0,
    max_w: int | None = None,
    max_bottom: int | None = None,
):
    """A small rounded banner/label, optionally rotated, centred on (cx, cy)."""
    text = text.upper()
    pad_x = int(height * 0.5)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    start_size = int(height * 0.5)
    min_size = int(height * 0.3)
    if max_w is not None:
        font = _fit_font_width(tmp, text, FONT_PATH_BOLD, max(1, max_w - pad_x * 2), start_size, min_size)
        font = _fit_font_height(tmp, text, FONT_PATH_BOLD, int(height * 0.6), font.size, min_size)
    else:
        font = _fit_font_height(tmp, text, FONT_PATH_BOLD, start_size, int(height * 0.6), min_size)
    b = tmp.textbbox((0, 0), text, font=font)
    tw, th = b[2] - b[0], b[3] - b[1]
    w = tw + pad_x * 2
    layer = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((0, 0, w, height), radius=height // 2, fill=bg)
    ld.text(((w - tw) / 2 - b[0], (height - th) / 2 - b[1]), text, fill=fg, font=font)
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    px = int(cx - layer.width / 2)
    py = int(cy - layer.height / 2)
    px = max(0, min(canvas.width - layer.width, px))
    if max_bottom is not None:
        py = min(py, max_bottom - layer.height)
    py = max(0, min(canvas.height - layer.height, py))
    canvas.alpha_composite(layer, (px, py))


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
    # Waschbär EDEKA house look: keep the original EDEKA Style structure, but
    # use anthracite as the base colour instead of a pure blue field.
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


def _draw_angebot_badge(
    canvas: Image.Image,
    cx: int,
    cy: int,
    height: int,
    accent: tuple[int, int, int],
    primary: tuple[int, int, int],
    label: str = "ANGEBOT",
):
    _draw_tag(canvas, label, cx, cy, height, accent, primary, angle=-7.0)


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


def _draw_product_or_name(canvas, draw, spec, product_zone, name_color, fill_scale: float = 0.96):
    product = _load_product_image(spec, (int(product_zone.w * fill_scale), int(product_zone.h * fill_scale)))
    if product:
        _draw_product(canvas, product, product_zone.cx, product_zone.cy, angle=0.0)
        return True
    else:
        ph = int(min(product_zone.w * 0.105, product_zone.h * 0.18))
        f = _fit_font_width(draw, spec.product.upper(), FONT_PATH_EXTRABOLD, int(product_zone.w * 0.70), ph, int(ph * 0.50))
        _draw_text_centered(draw, spec.product.upper(), product_zone.cx, product_zone.cy, f, name_color)
        return False


def _draw_validity_tag(canvas, spec, cx, cy, height, accent, primary):
    # Show the validity exactly as entered (e.g. "nur heute", "KW 24",
    # "bis 22.06.") — no automatic "nur" prefix.
    max_bottom = canvas.height - int(canvas.height * 0.125)
    max_w = int(canvas.width * 0.54)
    _draw_tag(canvas, spec.validity, cx, cy, height, accent, primary, angle=-3.0, max_w=max_w, max_bottom=max_bottom)


def _context_tags(spec: PromotionSpec) -> list[tuple[str, tuple[int, int, int], tuple[int, int, int]]]:
    """Derive realistic flyer badges (BIO / AUS DER REGION / NEU) from the spec."""
    if _is_event(spec):
        return []
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


def _draw_context_tags(
    canvas: Image.Image,
    spec: PromotionSpec,
    x_left: int,
    y_top: int,
    height: int,
    angle: float = -4.0,
    force_region: bool = False,
    brand_bg: tuple[int, int, int] | None = None,
    brand_fg: tuple[int, int, int] | None = None,
):
    """Stack up to two contextual badges, top-left anchored."""
    tags = _context_tags(spec)
    if force_region and not any(t[0] == "AUS DER REGION" for t in tags):
        tags.insert(0, ("AUS DER REGION", RED, (255, 255, 255)))
        tags = tags[:2]
    y = y_top
    for text, bg, fg in tags:
        if brand_bg is not None and brand_fg is not None:
            bg, fg = brand_bg, brand_fg
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
    pm, hm, am = _level_scale(spec)
    accent = _hsv_adjust(accent, am, 1.0)
    muted = _mix(ink, bg, 0.5)

    # Deep background with a faint product-tinted top and darker base + vignette.
    canvas.paste(_vertical_gradient((w, h), _mix(bg, glow, 0.08), _darken(bg, 0.4)), (0, 0))
    vig = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vig.putalpha(_radial_alpha(240, 0, 150, falloff=2.2).resize((w, h)))
    canvas.alpha_composite(vig)
    draw = ImageDraw.Draw(canvas)

    if tall:
        pz = Zone(margin, int(h * 0.13), w - margin * 2, int(h * 0.28))
        head_y = int(h * 0.63)
    else:
        pz = Zone(margin, int(h * 0.15), int(w * 0.58), int(h * 0.40))
        head_y = int(h * 0.61)

    # Spotlight: product-coloured glow + warm white core so the product pops.
    _draw_spotlight(canvas, pz.cx, pz.cy, int(pz.w * 0.62), glow, 120, falloff=1.9)
    _draw_spotlight(canvas, pz.cx, pz.cy, int(pz.w * 0.42), (255, 248, 232), 95, falloff=1.8)
    sw, sh_h = int(pz.w * 0.42), int(pz.h * 0.05)
    _draw_soft_shadow(canvas, pz.cx - sw // 2, int(pz.cy + pz.h * 0.34), sw, sh_h,
                      blur=max(16, pz.w // 14), intensity=110)
    # Luxe needs lots of negative space. If there is no product asset, do not
    # repeat the product name in the hero zone because the headline below
    # already carries it and the price seal must stay clear.
    product = _load_product_image(spec, (int(pz.w * 0.96), int(pz.h * 0.96)))
    if product:
        _draw_product(canvas, product, pz.cx, pz.cy, angle=0.0)

    # Brand lockup top-left (gold wordmark, mascot with halo on the dark bg).
    _draw_brand_lockup(canvas, margin, int(h * 0.055), int(h * (0.06 if tall else 0.078)), accent,
                       sub_color=muted, halo=True)
    # "ANGEBOT" kicker, top-right.
    kh = int(h * 0.02)
    label = _offer_label(spec)
    _draw_kicker(draw, w - margin - _kicker_width(draw, label, kh), int(h * 0.07), label, kh, accent)

    # Headline block, left: thin accent rule + product name + claim.
    draw.rectangle((margin, head_y, margin + int(w * 0.085), head_y + max(3, int(h * 0.006))), fill=accent)
    ny = head_y + int(h * 0.022)
    name_font, name_lines = _fit_wrapped(draw, spec.product.upper(), FONT_PATH_EXTRABOLD,
                                         int(w * 0.55), int(h * 0.16), int(h * 0.066 * hm), int(h * 0.034),
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

    # Price star (gold), the clear retail seal — bottom-right.
    ink_dark = (28, 26, 22)
    scx, scy = int(w * 0.75), int(h * (0.54 if tall else 0.52))
    sr = int(w * (0.165 if tall else 0.150) * min(pm, 1.05))
    _draw_price_star(canvas, spec, scx, scy, sr, ink_dark, accent, rot_deg=-7)
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        _draw_discount_burst(canvas, discount, int(scx - sr * 0.82), int(scy - sr * 0.9), int(sr * 0.5))
    _draw_validity_tag(canvas, spec, scx, int(scy + sr * 1.06), int(w * 0.05), accent, ink_dark)


def _product_accent(spec: PromotionSpec) -> tuple[int, int, int]:
    return _hsv_adjust(_product_dominant_color(_resolve_product_asset(spec)) or _hex_to_rgb("#1565C0"), 1.2, 0.95)


def _level_scale(spec: PromotionSpec) -> tuple[float, float, float]:
    """Kreativniveau -> (price size mul, headline size mul, accent saturation mul).
    Applies to every style so 'Dezent/Ausgewogen/Auffällig' is always visible."""
    lv = _enum_val(spec.differentiation_level)
    if lv == "bajo":       # Dezent: restrained
        return 0.82, 0.9, 0.78
    if lv == "alto":       # Auffällig: bigger, bolder, more saturated
        return 1.2, 1.12, 1.3
    return 1.0, 1.0, 1.0   # Ausgewogen


def _layout_editorial(canvas: Image.Image, spec: PromotionSpec, fmt: FormatType):
    """Light editorial style: airy background, product on a big colour disc that
    bleeds off the corner, dark oversized headline, clean round price seal."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    tall = h / w > 1.12
    accent = _product_accent(spec)
    pm, hm, am = _level_scale(spec)
    accent = _hsv_adjust(accent, am, 1.0)
    ink = (32, 32, 36)
    bg = _lighten(accent, 0.90)
    muted = _mix(ink, bg, 0.42)
    white = (255, 255, 255)
    margin = int(w * 0.075)

    canvas.paste(_vertical_gradient((w, h), _lighten(bg, 0.5), _darken(bg, 0.05)), (0, 0))

    if tall:
        disc_cx, disc_cy, disc_r = int(w * 0.74), int(h * 0.18), int(w * 0.62)
        prod = Zone(int(w * 0.08), int(h * 0.10), int(w * 0.84), int(h * 0.34))
        price_cx, price_cy, price_r = int(w * 0.74), int(h * 0.52), int(w * 0.205 * pm)
        head_y = int(h * 0.66)
    else:
        disc_cx, disc_cy, disc_r = int(w * 0.80), int(h * 0.18), int(w * 0.50)
        prod = Zone(int(w * 0.08), int(h * 0.14), int(w * 0.54), int(h * 0.48))
        price_cx, price_cy, price_r = int(w * 0.82), int(h * 0.60), int(w * 0.172 * pm)
        head_y = int(h * 0.62)

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

    # Price star (product colour), the clear retail seal — bottom-right.
    scx, scy = int(w * 0.77), int(h * (0.54 if tall else 0.56))
    sr = int(w * (0.178 if tall else 0.160) * min(pm, 1.05))
    _draw_price_star(canvas, spec, scx, scy, sr, ink, accent, rot_deg=-7)
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        _draw_discount_burst(canvas, discount, int(scx - sr * 0.82), int(scy - sr * 0.9), int(sr * 0.5))
    _draw_validity_tag(canvas, spec, scx, int(scy + sr * 1.06), int(w * 0.05), accent, _contrast_text(accent))

    # Kicker + accent rule + oversized headline + claim.
    kh = int(h * 0.02)
    _draw_kicker(draw, margin, head_y, (spec.category or "Aktion"), kh, accent)
    bar_y = head_y + int(kh * 1.8)
    draw.rounded_rectangle((margin, bar_y, margin + int(w * 0.11), bar_y + max(4, int(h * 0.009))), radius=h // 220, fill=accent)
    _draw_headline_block(draw, spec, Zone(margin, bar_y + int(h * 0.026), int(w * 0.58), int(h * 0.13)), ink, align="left", claim_color=muted)
    # (footer handled globally by the brand banner)


def _layout_colorblock(canvas: Image.Image, spec: PromotionSpec, fmt: FormatType):
    """Swiss/Bauhaus style: a bold colour block holds the product, the rest is
    white with strong typography. Geometric and graphic."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    tall = h / w > 1.12
    accent = _product_accent(spec)
    pm, hm, am = _level_scale(spec)
    accent = _hsv_adjust(accent, am, 1.0)
    ink = (24, 24, 26)
    white = (255, 255, 255)
    muted = (120, 120, 126)
    draw.rectangle((0, 0, w, h), fill=white)
    content_bottom = h - int(h * 0.145)

    if tall:
        # Top colour band holds the product; text column below.
        band_h = int(h * 0.44)
        draw.rectangle((0, 0, w, band_h), fill=accent)
        prod = Zone(int(w * 0.10), int(h * 0.045), int(w * 0.80), int(band_h - h * 0.09))
        col_x, col_w = int(w * 0.08), int(w * 0.84)
        head_y = int(band_h + h * 0.035)
        lock_color = white
        lock_y = int(h * 0.045)
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
    kh = int(h * (0.018 if tall else 0.02))
    _draw_kicker(draw, col_x, head_y, (spec.category or "Angebot"), kh, accent)
    name_font, name_lines = _fit_wrapped(draw, spec.product.upper(), FONT_PATH_EXTRABOLD,
                                         col_w, int(h * (0.16 if tall else 0.22)),
                                         int(h * (0.068 if tall else 0.085) * hm),
                                         int(h * (0.032 if tall else 0.04)),
                                         max_lines=2, line_spacing=1.0)
    ny = _draw_wrapped(draw, name_lines, col_x, col_w, head_y + int(kh * 1.9), name_font, ink, align="left", line_spacing=1.0)
    draw.rectangle((col_x, ny + int(h * 0.01), col_x + int(w * 0.10), ny + int(h * 0.01) + max(4, int(h * 0.01))), fill=accent)
    ny += int(h * 0.045)

    if spec.claim:
        cf = _load_font(FONT_PATH_REGULAR, int(h * (0.021 if tall else 0.026)))
        for line in _wrap_text(draw, spec.claim, cf, col_w, 1 if tall else 2):
            b = draw.textbbox((0, 0), line, font=cf)
            draw.text((col_x - b[0], ny - b[1]), line, fill=muted, font=cf)
            ny += int((b[3] - b[1]) * 1.35)
    ny += int(h * (0.014 if tall else 0.02))

    # Price block: statt + big price + validity/discount.
    old_h = int(h * (0.035 if tall else 0.042)) if spec.old_price and not _is_event(spec) else 0
    price_h = int(h * (0.105 if tall else 0.135))
    meta_h = int(h * (0.030 if tall else 0.036))
    price_block_h = old_h + price_h + meta_h
    if ny + price_block_h > content_bottom:
        ny = max(head_y + int(h * (0.17 if tall else 0.19)), content_bottom - price_block_h)
    if spec.old_price and not _is_event(spec):
        of = _load_font(FONT_PATH_REGULAR, int(h * (0.022 if tall else 0.026)))
        ot = f"statt {spec.old_price}"
        ob = draw.textbbox((0, 0), ot, font=of)
        draw.text((col_x - ob[0], ny - ob[1]), ot, fill=muted, font=of)
        draw.line((col_x, ny + (ob[3] - ob[1]) * 0.55, col_x + (ob[2] - ob[0]), ny + (ob[3] - ob[1]) * 0.55), fill=muted, width=max(2, h // 600))
        ny += int(h * (0.035 if tall else 0.042))
    value = _offer_value(spec)
    pf = _fit_font_width(draw, value, FONT_PATH_EXTRABOLD, col_w, int(h * (0.088 if tall else 0.112) * pm), int(h * (0.050 if tall else 0.062)))
    pb = draw.textbbox((0, 0), value, font=pf)
    draw.text((col_x - pb[0], ny - pb[1]), value, fill=accent, font=pf)
    ny += int((pb[3] - pb[1]) + h * (0.012 if tall else 0.02))

    meta = spec.validity.upper()
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        meta = f"{meta}   ·   −{discount}%"
    mf = _load_font(FONT_PATH_SEMIBOLD, int(h * (0.017 if tall else 0.02)))
    mb = draw.textbbox((0, 0), meta, font=mf)
    draw.text((col_x - mb[0], ny - mb[1]), meta, fill=ink, font=mf)

    # Context badge just under the meta line (kept clear of the footer banner).
    ctx = _context_tags(spec)
    if ctx and ny + int(h * 0.075) < content_bottom:
        _draw_kicker(draw, col_x, ny + int(h * 0.05), ctx[0][0], int(h * 0.016), accent)


def _duotone(img: Image.Image, dark: tuple[int, int, int], light: tuple[int, int, int]) -> Image.Image:
    img = img.convert("RGBA")
    alpha = img.getchannel("A")
    duo = ImageOps.colorize(img.convert("L"), black=dark, white=light).convert("RGBA")
    duo.putalpha(alpha)
    return duo


def _paste_product(canvas, spec, zone, shadow=70, duotone=None, name_color=(40, 40, 40)) -> bool:
    img = _load_product_image(spec, (int(zone.w * 0.96), int(zone.h * 0.96)))
    if img is None:
        draw = ImageDraw.Draw(canvas)
        f = _fit_font_width(draw, spec.product.upper(), FONT_PATH_EXTRABOLD, int(zone.w * 0.85), int(zone.w * 0.14), int(zone.w * 0.07))
        _draw_text_centered(draw, spec.product.upper(), zone.cx, zone.cy, f, name_color)
        return False
    if duotone:
        img = _duotone(img, duotone[0], duotone[1])
    x = zone.cx - img.width // 2
    y = zone.cy - img.height // 2
    if shadow:
        sw, shh = int(img.width * 0.5), int(img.height * 0.06)
        _draw_soft_shadow(canvas, x + (img.width - sw) // 2, y + img.height - shh, sw, shh,
                          blur=max(12, img.width // 15), intensity=shadow)
    canvas.alpha_composite(img, (x, y))
    return True


def _draw_brand_top(canvas, x, y, mascot_h, color, halo=False) -> None:
    """Compact lockup: mascot + EDEKA Mühlenbein (used by the extra styles)."""
    _draw_brand_lockup(canvas, x, y, mascot_h, color, sub_color=_mix(color, (128, 128, 128), 0.4), halo=halo)


def _layout_lifestyle(canvas: Image.Image, spec: PromotionSpec, fmt: FormatType):
    """Warm natural 'market' look: linen/wood background, soft daylight, the
    product grounded with a natural shadow, warm earthy type."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    tall = h / w > 1.12
    margin = int(w * 0.08)
    pm, hm, am = _level_scale(spec)
    accent = _hsv_adjust(_product_accent(spec), 0.95 * am, 0.85)
    ink = (58, 44, 30)
    muted = (120, 104, 84)
    white = (252, 248, 240)

    canvas.paste(_vertical_gradient((w, h), (240, 231, 216), (212, 194, 166)), (0, 0))
    _draw_spotlight(canvas, int(w * 0.5), int(h * 0.30), int(max(w, h) * 0.5), (255, 250, 236), 110, falloff=2.0)
    vig = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vig.putalpha(_radial_alpha(240, 0, 70, falloff=2.4).resize((w, h)))
    canvas.alpha_composite(Image.composite(Image.new("RGBA", (w, h), (60, 44, 28, 255)), Image.new("RGBA", (w, h), (0, 0, 0, 0)), vig))
    draw = ImageDraw.Draw(canvas)

    if tall:
        pz = Zone(margin, int(h * 0.12), w - margin * 2, int(h * 0.32))
        price_cx, price_cy, price_r = int(w * 0.74), int(h * 0.56), int(w * 0.178 * pm)
        head_y = int(h * 0.60)
    else:
        pz = Zone(margin, int(h * 0.14), int(w * 0.56), int(h * 0.44))
        price_cx, price_cy, price_r = int(w * 0.80), int(h * 0.66), int(w * 0.160 * pm)
        head_y = int(h * 0.64)

    _paste_product(canvas, spec, pz, shadow=120, name_color=ink)
    _draw_brand_top(canvas, margin, int(h * 0.05), int(h * (0.058 if tall else 0.075)), ink)
    _draw_context_tags(canvas, spec, margin, int(h * (0.13 if tall else 0.16)), int(w * 0.05))

    kh = int(h * 0.02)
    _draw_kicker(draw, margin, head_y, (spec.category or "Frisch"), kh, accent)
    bar_y = head_y + int(kh * 1.9)
    draw.rounded_rectangle((margin, bar_y, margin + int(w * 0.10), bar_y + max(4, int(h * 0.009))), radius=h // 220, fill=accent)
    _draw_headline_block(draw, spec, Zone(margin, bar_y + int(h * 0.026), int(w * 0.58), int(h * 0.13)), ink, align="left", claim_color=muted)

    # Price star (warm), the clear retail seal — bottom-right.
    scx, scy = int(w * 0.77), int(h * (0.55 if tall else 0.58))
    sr = int(w * (0.168 if tall else 0.154) * min(pm, 1.05))
    _draw_price_star(canvas, spec, scx, scy, sr, ink, accent, rot_deg=-7)
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        _draw_discount_burst(canvas, discount, int(scx - sr * 0.82), int(scy - sr * 0.9), int(sr * 0.5))
    _draw_validity_tag(canvas, spec, scx, int(scy + sr * 1.06), int(w * 0.05), accent, _contrast_text(accent))


def _layout_magazine(canvas: Image.Image, spec: PromotionSpec, fmt: FormatType):
    """Editorial magazine / duotone: product recoloured into two tones, big
    masthead typography, thin rules. Arty and high-end."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    tall = h / w > 1.12
    margin = int(w * 0.08)
    pm, hm, am = _level_scale(spec)
    accent = _hsv_adjust(_product_accent(spec), am, 1.0)
    deep = _hsv_adjust(accent, 0.95, 0.42)
    cream = (243, 239, 229)
    ink = deep
    muted = _mix(deep, cream, 0.4)

    canvas.paste(_vertical_gradient((w, h), cream, _darken(cream, 0.04)), (0, 0))
    draw = ImageDraw.Draw(canvas)

    # Masthead rule + EDEKA wordmark, top.
    top = int(h * 0.06)
    draw.line((margin, top, w - margin, top), fill=deep, width=max(2, h // 360))
    mh = int(h * (0.05 if tall else 0.062))
    _draw_brand_top(canvas, margin, top + int(h * 0.012), mh, deep)
    kk = _offer_label(spec)
    _draw_kicker(draw, w - margin - _kicker_width(draw, kk, int(h * 0.018)), top + int(h * 0.022), kk, int(h * 0.018), accent)

    if tall:
        pz = Zone(margin, int(h * 0.13), w - margin * 2, int(h * 0.34))
        head_y = int(h * 0.51)
    else:
        pz = Zone(int(w * 0.30), int(h * 0.16), int(w * 0.66), int(h * 0.50))
        head_y = int(h * 0.40)

    _paste_product(canvas, spec, pz, shadow=0, duotone=(deep, cream), name_color=deep)

    # Oversized masthead headline.
    hx = margin
    hw = int(w * (0.84 if tall else 0.40))
    nf, nl = _fit_wrapped(draw, spec.product.upper(), FONT_PATH_EXTRABOLD, hw, int(h * 0.24),
                          int(h * 0.10 * hm), int(h * 0.05), max_lines=2, line_spacing=0.98)
    ny = _draw_wrapped(draw, nl, hx, hw, head_y, nf, ink, align="left", line_spacing=0.98)
    if spec.claim:
        cf = _load_font(FONT_PATH_REGULAR, int(h * 0.026))
        for line in _wrap_text(draw, spec.claim, cf, hw, 2):
            b = draw.textbbox((0, 0), line, font=cf)
            draw.text((hx - b[0], ny + int(h * 0.012) - b[1]), line, fill=muted, font=cf)
            ny += int((b[3] - b[1]) * 1.3)
    ny += int(h * 0.02)

    # Price: big number + struck old price, magazine style.
    if spec.old_price and not _is_event(spec):
        of = _load_font(FONT_PATH_REGULAR, int(h * 0.028))
        ot = f"statt {spec.old_price}"
        ob = draw.textbbox((0, 0), ot, font=of)
        draw.text((hx - ob[0], ny - ob[1]), ot, fill=muted, font=of)
        draw.line((hx, ny + (ob[3] - ob[1]) * 0.55, hx + (ob[2] - ob[0]), ny + (ob[3] - ob[1]) * 0.55), fill=muted, width=max(2, h // 600))
        ny += int(h * 0.045)
    value = _offer_value(spec)
    pf = _fit_font_width(draw, value, FONT_PATH_EXTRABOLD, hw, int(h * 0.13 * pm), int(h * 0.064))
    pb = draw.textbbox((0, 0), value, font=pf)
    draw.text((hx - pb[0], ny - pb[1]), value, fill=accent, font=pf)
    # validity, small, under the price (footer is the global brand banner)
    vf = _load_font(FONT_PATH_SEMIBOLD, int(h * 0.02))
    vb = draw.textbbox((0, 0), spec.validity.upper(), font=vf)
    draw.text((hx - vb[0], ny + int((pb[3] - pb[1]) * 1.2) - vb[1]), spec.validity.upper(), fill=muted, font=vf)


RETRO_ACCENTS = {
    "fresco": (216, 154, 46),    # mustard
    "premium": (38, 110, 102),   # teal
    "atrevido": (198, 82, 40),   # burnt orange
    "local": (150, 92, 44),      # brown
}


def _layout_retro(canvas: Image.Image, spec: PromotionSpec, fmt: FormatType):
    """Retro / vintage: aged cream paper, sunburst, starburst price seal,
    heavy headline and a double border."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    tall = h / w > 1.12
    margin = int(w * 0.07)
    cream = (243, 230, 202)
    ink = (58, 40, 22)
    pm, hm, am = _level_scale(spec)
    accent = _hsv_adjust(RETRO_ACCENTS.get(_enum_val(spec.tone), RETRO_ACCENTS["fresco"]), am, 1.0)
    deep = _darken(accent, 0.2)

    canvas.paste(_vertical_gradient((w, h), _lighten(cream, 0.2), _darken(cream, 0.06)), (0, 0))
    # faint retro sunburst rays from centre
    _draw_retro_rays(canvas, w // 2, int(h * 0.42), int(max(w, h) * 0.8), 36, _mix(accent, cream, 0.55))
    # double border
    for i, off in enumerate((int(w * 0.035), int(w * 0.045))):
        wdt = max(2, w // (300 if i == 0 else 900))
        draw.rectangle((off, off, w - off, h - off), outline=ink, width=wdt)
    draw = ImageDraw.Draw(canvas)

    if tall:
        pz = Zone(margin * 2, int(h * 0.13), w - margin * 4, int(h * 0.30))
        star_cx, star_cy, star_r = int(w * 0.72), int(h * 0.56), int(w * 0.155 * min(pm, 1.05))
        head_y = int(h * 0.66)
    else:
        pz = Zone(margin * 2, int(h * 0.14), int(w * 0.54), int(h * 0.42))
        star_cx, star_cy, star_r = int(w * 0.78), int(h * 0.66), int(w * 0.135 * min(pm, 1.05))
        head_y = int(h * 0.68)

    _paste_product(canvas, spec, pz, shadow=70, name_color=ink)

    # Vintage wordmark top-centre.
    _draw_brand_top(canvas, margin * 2, int(h * 0.06), int(h * (0.055 if tall else 0.07)), ink)
    _draw_kicker(draw, w - margin * 2 - _kicker_width(draw, "SEIT 1907", int(h * 0.016)), int(h * 0.075), "SEIT 1907", int(h * 0.016), deep)

    # Heavy headline + claim.
    kh = int(h * 0.02)
    _draw_kicker(draw, margin * 2, head_y, (spec.category or "Frischemarkt"), kh, deep)
    nf, nl = _fit_wrapped(draw, spec.product.upper(), FONT_PATH_EXTRABOLD, int(w * 0.5), int(h * 0.2),
                          int(h * 0.085 * hm), int(h * 0.045), max_lines=2, line_spacing=1.0)
    ny = _draw_wrapped(draw, nl, margin * 2, int(w * 0.5), head_y + int(kh * 1.9), nf, ink, align="left", line_spacing=1.0)
    if spec.claim:
        cf = _load_font(FONT_PATH_SEMIBOLD, int(h * 0.024))
        for line in _wrap_text(draw, spec.claim, cf, int(w * 0.46), 2):
            b = draw.textbbox((0, 0), line, font=cf)
            draw.text((margin * 2 - b[0], ny + int(h * 0.012) - b[1]), line, fill=deep, font=cf)
            ny += int((b[3] - b[1]) * 1.3)

    # Starburst price seal in retro colours.
    _draw_price_star(canvas, spec, star_cx, star_cy, star_r, ink, accent, rot_deg=-6)
    # (footer handled globally by the brand banner)


def _draw_retro_rays(canvas, cx, cy, radius, rays, color):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    step = math.pi / rays
    for i in range(rays):
        a0 = 2 * step * i
        a1 = a0 + step
        d.polygon([(cx, cy), (cx + radius * math.cos(a0), cy + radius * math.sin(a0)),
                   (cx + radius * math.cos(a1), cy + radius * math.sin(a1))], fill=(*color, 90))
    canvas.alpha_composite(layer)


@dataclass
class StyleConfig:
    primary: tuple[int, int, int]
    secondary: tuple[int, int, int]
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


def _build_style_config(
    spec: PromotionSpec,
    primary,
    accent,
    style: str = "edeka",
    secondary: tuple[int, int, int] | None = None,
) -> StyleConfig:
    """Translate Tonalität (mood/colour) and Kreativniveau (intensity) into
    concrete drawing parameters."""
    tone = _enum_val(spec.tone)
    level = _enum_val(spec.differentiation_level)
    edeka = style == "edeka"
    secondary = secondary or _hex_to_rgb(BRAND_BLUE)

    bg_light, bg_dark, vignette = 0.13, 0.42, 130
    star_scale, halo, spot = 1.0, 120, 165
    force_region = False

    # --- Tonalität: mood (colour tweaks only for EDEKA Style; Kreativ already
    #     uses a distinct colour theme per tone) ---
    if tone == "premium":          # elegant, deep
        if edeka:
            primary = _darken(primary, 0.06)
            secondary = _darken(secondary, 0.14)
            accent = _mix(accent, (255, 176, 32), 0.28)
        bg_light, bg_dark, vignette = 0.04, 0.52, 185
        star_scale *= 0.95
    elif tone == "atrevido":       # Mutig: louder, bigger, brighter
        if edeka:
            primary = _lighten(primary, 0.04)
            secondary = _lighten(secondary, 0.10)
        star_scale *= 1.12
        halo += 45
        spot += 25
    elif tone == "local":          # warm + always show the region badge
        if edeka:
            secondary = _mix(secondary, primary, 0.16)
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
    elif level == "alto":          # Auffällig: maximum impact without crowding
        star_scale *= 1.02
        halo = int(halo * 1.45)
        spot = int(spot * 1.2)

    return StyleConfig(primary, secondary, accent, bg_light, bg_dark, vignette,
                       round(star_scale, 3), halo, spot, force_region)


def _layout_post(canvas: Image.Image, spec: PromotionSpec, cfg: StyleConfig):
    w, h = canvas.size
    margin = int(w * 0.05)
    white = (255, 255, 255)
    primary, accent = cfg.primary, cfg.accent
    _paint_background(canvas, cfg)
    draw = ImageDraw.Draw(canvas)

    # Soft warm halo behind the star (intensity from Kreativniveau).
    star_cx, star_cy, star_r = int(w * 0.77), int(h * 0.47), int(w * 0.22 * cfg.star_scale)
    _draw_spotlight(canvas, star_cx, star_cy, int(star_r * 1.7), _lighten(accent, 0.45), cfg.halo_alpha)

    _draw_brand_lockup(canvas, margin, int(h * 0.05), int(h * 0.10), accent)
    _draw_angebot_badge(canvas, int(w * 0.83), int(h * 0.085), int(h * 0.058), accent, primary, _offer_label(spec))

    # Product hero on the left, lifted by a warm spotlight.
    _draw_spotlight(canvas, int(w * 0.28), int(h * 0.42), int(w * 0.32), _lighten(accent, 0.5), cfg.spotlight_alpha)
    _draw_product_or_name(canvas, draw, spec, Zone(int(w * 0.04), int(h * 0.20), int(w * 0.46), int(h * 0.40)), white, fill_scale=1.02)

    _draw_context_tags(canvas, spec, margin, int(h * 0.205), int(w * 0.052), force_region=cfg.force_region, brand_bg=accent, brand_fg=primary)

    _draw_price_star(canvas, spec, star_cx, star_cy, star_r, cfg.secondary, accent)
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        _draw_discount_burst_colored(canvas, discount, int(star_cx - star_r * 0.78), int(star_cy - star_r * 0.88), int(star_r * 0.46), cfg.secondary, accent)
    _draw_validity_tag(canvas, spec, star_cx, int(star_cy + star_r * 1.0), int(w * 0.052), accent, primary)

    _draw_headline_block(draw, spec, Zone(margin, int(h * 0.70), int(w * 0.62), int(h * 0.14)), white, align="left", claim_color=CLAIM_LIGHT)
    # (footer handled globally by the brand banner)


def _layout_story(canvas: Image.Image, spec: PromotionSpec, cfg: StyleConfig):
    w, h = canvas.size
    margin = int(w * 0.06)
    white = (255, 255, 255)
    primary, accent = cfg.primary, cfg.accent
    _paint_background(canvas, cfg)
    draw = ImageDraw.Draw(canvas)

    # Vertical formats keep the square-post logic: product fills the left side,
    # while the price dominates the right-middle instead of floating alone.
    star_cx, star_cy, star_r = int(w * 0.68), int(h * 0.49), int(w * 0.235 * cfg.star_scale)
    _draw_spotlight(canvas, star_cx, star_cy, int(star_r * 1.8), _lighten(accent, 0.45), cfg.halo_alpha)

    _draw_brand_lockup(canvas, margin, int(h * 0.04), int(h * 0.072), accent)
    _draw_angebot_badge(canvas, int(w * 0.78), int(h * 0.066), int(h * 0.04), accent, primary, _offer_label(spec))

    _draw_spotlight(canvas, int(w * 0.34), int(h * 0.365), int(w * 0.45), _lighten(accent, 0.5), cfg.spotlight_alpha)
    _draw_product_or_name(canvas, draw, spec, Zone(int(w * 0.035), int(h * 0.165), int(w * 0.68), int(h * 0.43)), white, fill_scale=1.04)
    _draw_context_tags(canvas, spec, margin, int(h * 0.145), int(w * 0.052), force_region=cfg.force_region, brand_bg=accent, brand_fg=primary)

    _draw_price_star(canvas, spec, star_cx, star_cy, star_r, cfg.secondary, accent)
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        _draw_discount_burst_colored(canvas, discount, int(star_cx + star_r * 0.70), int(star_cy - star_r * 0.78), int(star_r * 0.35), cfg.secondary, accent)

    _draw_validity_tag(canvas, spec, star_cx, int(star_cy + star_r * 1.04), int(w * 0.052), accent, primary)
    _draw_headline_block(draw, spec, Zone(margin, int(h * 0.68), int(w * 0.84), int(h * 0.14)), white, align="left", claim_color=CLAIM_LIGHT)
    # (footer handled globally by the brand banner)


def _layout_poster(canvas: Image.Image, spec: PromotionSpec, cfg: StyleConfig):
    w, h = canvas.size
    margin = int(w * 0.06)
    white = (255, 255, 255)
    primary, accent = cfg.primary, cfg.accent
    _paint_background(canvas, cfg)
    draw = ImageDraw.Draw(canvas)

    star_cx, star_cy, star_r = int(w * 0.69), int(h * 0.475), int(w * 0.238 * cfg.star_scale)
    _draw_spotlight(canvas, star_cx, star_cy, int(star_r * 1.9), _lighten(accent, 0.45), cfg.halo_alpha)

    _draw_brand_lockup(canvas, margin, int(h * 0.035), int(h * 0.060), accent)
    _draw_angebot_badge(canvas, int(w * 0.80), int(h * 0.052), int(h * 0.034), accent, primary, _offer_label(spec))

    _draw_spotlight(canvas, int(w * 0.34), int(h * 0.35), int(w * 0.45), _lighten(accent, 0.5), cfg.spotlight_alpha)
    _draw_product_or_name(canvas, draw, spec, Zone(int(w * 0.02), int(h * 0.115), int(w * 0.70), int(h * 0.455)), white, fill_scale=1.04)
    _draw_context_tags(canvas, spec, margin, int(h * 0.105), int(w * 0.046), force_region=cfg.force_region, brand_bg=accent, brand_fg=primary)

    _draw_price_star(canvas, spec, star_cx, star_cy, star_r, cfg.secondary, accent)
    discount = _discount_percent(spec.old_price or "", spec.price)
    if discount:
        _draw_discount_burst_colored(canvas, discount, int(star_cx + star_r * 0.70), int(star_cy - star_r * 0.78), int(star_r * 0.35), cfg.secondary, accent)

    _draw_validity_tag(canvas, spec, star_cx, int(star_cy + star_r * 1.05), int(w * 0.046), accent, primary)
    _draw_headline_block(draw, spec, Zone(margin, int(h * 0.705), int(w * 0.76), int(h * 0.13)), white, align="left", claim_color=CLAIM_LIGHT)
    # (footer handled globally by the brand banner)


def _auto_ai_style(spec: PromotionSpec, direction: CreativeDirection) -> str:
    """Pick a renderer for AI mode from the AI direction, without exposing templates in the UI."""
    text = _normalize(
        " ".join([
            spec.product,
            spec.category or "",
            spec.claim or "",
            spec.tone.value,
            direction.name,
            direction.intent,
            direction.composition,
            direction.boldness,
        ])
    )
    if _is_event(spec):
        if any(word in text for word in ["premium", "elegant", "abend", "wein", "luxe"]):
            return "luxe"
        if any(word in text for word in ["community", "markt", "event", "aktion", "grafisch", "plakat"]):
            return "colorblock"
        return "editorial"
    if any(word in text for word in ["premium", "elegant", "hochwert", "luxe"]):
        return "luxe"
    if any(word in text for word in ["natuerlich", "frisch", "markt", "regional", "lifestyle"]):
        return "lifestyle"
    if any(word in text for word in ["magazin", "editorial", "klar", "clean"]):
        return "editorial"
    if any(word in text for word in ["retro", "vintage"]):
        return "retro"
    if any(word in text for word in ["grafisch", "block", "bauhaus", "plakat"]):
        return "colorblock"
    return "editorial"


# ---------------------------------------------------------------------------
# AI-driven layout: generative scene + strict content zones
# ---------------------------------------------------------------------------

def _ai_palette(spec: PromotionSpec, direction: CreativeDirection) -> tuple[
    tuple[int, int, int],
    tuple[int, int, int],
    tuple[int, int, int],
    tuple[int, int, int],
]:
    product_color = _hex_to_rgb(BRAND_BLUE) if _is_event(spec) else (_product_dominant_color(_resolve_product_asset(spec)) or _hex_to_rgb(BRAND_BLUE))
    palette = list(direction.palette or [])
    while len(palette) < 4:
        palette.append("#FFFFFF")

    primary = _hex_to_rgb(palette[0], _hex_to_rgb(BRAND_BLUE))
    accent = _hex_to_rgb(palette[1], _hex_to_rgb(BRAND_YELLOW))
    theme = _hex_to_rgb(palette[2], product_color)
    paper = _hex_to_rgb(palette[3], (249, 247, 241))

    # Keep the AI wild, but within usable retail contrast.
    if _luminance(primary) > 170:
        primary = _darken(primary, 0.42)
    if _luminance(accent) < 120:
        accent = _mix(accent, _hex_to_rgb(BRAND_YELLOW), 0.62)
    if _luminance(theme) < 55:
        theme = _lighten(theme, 0.35)
    if _luminance(paper) < 155:
        paper = _lighten(paper, 0.72)
    return primary, accent, _hsv_adjust(theme, 1.18, 1.0), paper


# ---------------------------------------------------------------------------
# Editorial creative system (AI mode)
#
# The AI layouts are built like real posters: the photo (or a designed graphic
# field) fills the frame, a cinematic colour grade fuses type and image, and the
# message lives directly ON the artwork as a confident typographic hierarchy —
# not a collage of rounded cards. One accent colour (EDEKA yellow) carries the
# marketing pop; everything else stays disciplined.
# ---------------------------------------------------------------------------

DISPLAY_INK = (12, 19, 32)      # deep cinematic navy-black for grades
WARM_WHITE = (247, 245, 239)


def _tracked_text(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font, fill, tracking: int) -> int:
    """Draw letter-spaced caps (an editorial eyebrow). Returns the width drawn."""
    cx = x
    for ch in text:
        draw.text((cx, y), ch, font=font, fill=fill)
        cx += draw.textlength(ch, font=font) + tracking
    return int(cx - tracking - x) if text else 0


def _vignette(canvas: Image.Image, strength: int = 70):
    w, h = canvas.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse((int(-w * 0.18), int(-h * 0.18), int(w * 1.18), int(h * 1.18)), fill=255)
    mask = mask.point(lambda a: 255 - a).filter(ImageFilter.GaussianBlur(radius=max(20, w // 26)))
    layer = Image.new("RGBA", (w, h), (4, 7, 12, 0))
    layer.putalpha(mask.point(lambda a: int(a / 255 * strength)))
    canvas.alpha_composite(layer)


def _grade_photo(canvas: Image.Image, image_path: Path, primary: tuple[int, int, int]):
    """Full-bleed hero photo, kept clean. Only a light top scrim for the brand
    mark and a dark base behind the footer — the content card brings its own
    legible surface, so the image itself is never flooded with text."""
    w, h = canvas.size
    try:
        photo = _cover_image(Image.open(image_path), (w, h)).convert("RGB")
    except Exception:  # noqa: BLE001
        canvas.paste(_diagonal_gradient((w, h), _darken(primary, 0.05), _darken(primary, 0.5)), (0, 0))
        return
    photo = ImageEnhance.Color(photo).enhance(0.97)
    photo = ImageEnhance.Contrast(photo).enhance(1.05)
    canvas.paste(photo, (0, 0))

    ink = _mix(DISPLAY_INK, _darken(primary, 0.55), 0.40)
    # Light top scrim so the brand lockup always reads on the clean photo.
    top = Image.new("L", (1, h), 0)
    tp = top.load()
    for yy in range(h):
        tp[0, yy] = int(max(0.0, min(1.0, 1.0 - yy / (h * 0.20))) * 135)
    tscrim = Image.new("RGBA", (w, h), (*ink, 0))
    tscrim.putalpha(top.resize((w, h)))
    canvas.alpha_composite(tscrim)
    # Dark base under the global footer band so it stays cohesive.
    base = Image.new("L", (1, h), 0)
    bp = base.load()
    for yy in range(h):
        t = (yy / max(1, h - 1) - 0.82) / 0.18
        bp[0, yy] = int(max(0.0, min(1.0, t)) * 220)
    bscrim = Image.new("RGBA", (w, h), (*ink, 0))
    bscrim.putalpha(base.resize((w, h)))
    canvas.alpha_composite(bscrim)
    _vignette(canvas, 62)


def _halftone(canvas: Image.Image, color: tuple[int, int, int]):
    """Top-right halftone dots — a subtle retail texture for the no-photo field."""
    w, h = canvas.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    step = max(16, w // 36)
    r0 = step * 0.18
    for yy in range(0, int(h * 0.46), step):
        for xx in range(int(w * 0.56), w, step):
            fade = ((xx - w * 0.56) / (w * 0.44)) * (1.0 - yy / (h * 0.46))
            if fade <= 0:
                continue
            r = r0 * (0.35 + fade)
            d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(*color, int(64 * fade)))
    canvas.alpha_composite(layer)


def _graphic_backdrop(canvas: Image.Image, spec: PromotionSpec, primary: tuple[int, int, int], accent: tuple[int, int, int], theme: tuple[int, int, int]):
    """Calm designed field for events with no photo: a diagonal brand grade with
    one accent slash and subtle halftone — a clean stage for the content card."""
    w, h = canvas.size
    base = _mix(DISPLAY_INK, _darken(primary, 0.30), 0.55)
    canvas.paste(_diagonal_gradient((w, h), _darken(base, 0.0), _darken(base, 0.5)), (0, 0))
    slash = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    _aa_polygon(slash, [(0, int(h * 0.30)), (w, int(h * 0.12)), (w, int(h * 0.155)), (0, int(h * 0.335))], fill=(*accent, 38))
    canvas.alpha_composite(slash)
    _halftone(canvas, accent)
    _draw_spotlight(canvas, int(w * 0.24), int(h * 0.24), int(max(w, h) * 0.30), _lighten(accent, 0.2), 38, 2.4)
    _draw_spotlight(canvas, int(w * 0.80), int(h * 0.36), int(max(w, h) * 0.26), _lighten(primary, 0.25), 36, 2.6)
    _vignette(canvas, 66)


def _product_backdrop(canvas: Image.Image, primary: tuple[int, int, int], theme: tuple[int, int, int]):
    """Premium retail backdrop: a graded brand field with a spotlight behind the
    product so the cut-out reads as a hero, plus a bottom scrim that anchors the
    type block in a dark, legible zone."""
    w, h = canvas.size
    top = _mix(_darken(primary, 0.04), DISPLAY_INK, 0.22)
    canvas.paste(_diagonal_gradient((w, h), top, _darken(primary, 0.46)), (0, 0))
    _draw_spotlight(canvas, int(w * 0.5), int(h * 0.34), int(max(w, h) * 0.46), _lighten(primary, 0.42), 100, 1.7)
    _draw_spotlight(canvas, int(w * 0.84), int(h * 0.80), int(max(w, h) * 0.28), theme, 36, 2.5)
    ink = _mix(DISPLAY_INK, _darken(primary, 0.5), 0.5)
    grad = Image.new("L", (1, h), 0)
    gp = grad.load()
    for yy in range(h):
        t = (yy / max(1, h - 1) - 0.46) / 0.54
        gp[0, yy] = int(max(0.0, min(1.0, t)) ** 1.3 * 214)
    scrim = Image.new("RGBA", (w, h), (*ink, 0))
    scrim.putalpha(grad.resize((w, h)))
    canvas.alpha_composite(scrim)
    _vignette(canvas, 72)


def _draw_poster_frame(canvas: Image.Image, margin: int, rgba: tuple[int, int, int, int], bottom: int):
    w, _ = canvas.size
    inset = int(margin * 0.55)
    ImageDraw.Draw(canvas, "RGBA").rectangle(
        (inset, inset, w - inset, bottom - inset), outline=rgba, width=max(2, w // 640)
    )


def _draw_cutout(canvas: Image.Image, img: Image.Image, cx: int, cy: int, max_size: tuple[int, int], angle: float = 0.0):
    im = img.copy()
    im.thumbnail(max_size, Image.Resampling.LANCZOS)
    if angle:
        im = im.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    x = cx - im.width // 2
    y = cy - im.height // 2
    sw = int(im.width * 0.80)
    sh = max(10, int(im.height * 0.12))
    _draw_soft_shadow(canvas, x + (im.width - sw) // 2, y + int(im.height * 0.84), sw, sh, blur=max(12, im.width // 16), intensity=125)
    canvas.alpha_composite(im, (x, y))


def _draw_kicker(canvas: Image.Image, x: int, y: int, label: str, h: int, accent: tuple[int, int, int]) -> int:
    """Accent rule + letter-spaced eyebrow. Returns the bottom y."""
    draw = ImageDraw.Draw(canvas)
    rule_w = int(h * 2.1)
    rule_h = max(3, h // 6)
    draw.rectangle((x, y, x + rule_w, y + rule_h), fill=accent)
    ky = y + rule_h + int(h * 0.30)
    kf = _load_font(FONT_PATH_DISPLAY_MED, int(h * 0.66))
    _tracked_text(draw, x, ky, label.upper(), kf, WARM_WHITE, max(2, int(h * 0.11)))
    return ky + int(h * 0.66) + int(h * 0.12)


def _fit_headline(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, max_lines: int = 3):
    # Allow long hyphenated titles (e.g. SCHOKOLADEN-VERKOSTUNG) to break at the
    # hyphen, then restore the hyphen on any line that stayed whole.
    wrappable = re.sub(r"-(?=\S)", "- ", text)
    font, lines = _fit_wrapped(
        draw, wrappable, FONT_PATH_DISPLAY, max_w, max_h,
        start_size=int(max_h), min_size=int(max_h * 0.16),
        max_lines=max_lines, line_spacing=0.84,
    )
    lines = [ln.replace("- ", "-") for ln in lines]
    line_h = _text_size(draw, "ÁgMy", font)[1]
    total = int(line_h * 0.84 * (len(lines) - 1)) + line_h
    widest = max((_text_size(draw, ln, font)[0] for ln in lines), default=0)
    return font, lines, line_h, total, widest


def _draw_headline(canvas: Image.Image, x: int, y: int, font, lines: list[str], line_h: int, fill=(255, 255, 255), shadow: int = 150) -> int:
    draw = ImageDraw.Draw(canvas)
    cy = y
    for line in lines:
        draw.text((x + max(2, line_h // 40), cy + max(2, line_h // 30)), line, font=font, fill=(0, 0, 0, shadow))
        draw.text((x, cy), line, font=font, fill=fill)
        cy += int(line_h * 0.84)
    return cy


def _panel_mask(size: tuple[int, int], radius: int, round_bottom: bool = True) -> Image.Image:
    w, h = size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    if not round_bottom:
        d.rectangle((0, h - radius - 1, w - 1, h - 1), fill=255)
    return m


def _glass_panel(canvas: Image.Image, box, radius: int, accent: tuple[int, int, int], round_bottom: bool = True):
    """A premium frosted-glass content card: the photo behind is blurred and
    darkened so the image shows through softly while the type stays crisp. A
    hairline highlight and a soft drop shadow lift it off the artwork."""
    x0, y0, x1, y1 = (int(v) for v in box)
    w, h = canvas.size
    cw, ch = x1 - x0, y1 - y0
    # drop shadow lifts the card off the photo
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + max(6, ch // 50), x1, y1 + max(6, ch // 50)), radius=radius, fill=(0, 0, 0, 110))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=max(12, cw // 26))))
    # frosted region: blurred crop + dark vertical tint for legibility
    region = canvas.crop((x0, y0, x1, y1)).convert("RGB").filter(ImageFilter.GaussianBlur(radius=max(14, cw // 12)))
    region = region.convert("RGBA")
    tg = Image.new("L", (1, ch), 0)
    tp = tg.load()
    for yy in range(ch):
        tp[0, yy] = int(168 + 72 * (yy / max(1, ch - 1)))
    tint = Image.new("RGBA", (cw, ch), (*DISPLAY_INK, 0))
    tint.putalpha(tg.resize((cw, ch)))
    region.alpha_composite(tint)
    region.putalpha(_panel_mask((cw, ch), radius, round_bottom))
    canvas.alpha_composite(region, (x0, y0))
    d = ImageDraw.Draw(canvas, "RGBA")
    d.rounded_rectangle((x0, y0, x1, y1), radius=radius, outline=(255, 255, 255, 40), width=max(2, w // 1000))
    d.line((x0 + radius, y0 + max(2, h // 1100), x1 - radius, y0 + max(2, h // 1100)), fill=(255, 255, 255, 60), width=max(1, h // 2000))


def _icon_pin(canvas: Image.Image, cx: int, cy: int, s: int, color: tuple[int, int, int]):
    S = 4
    tile = Image.new("RGBA", (s * S, s * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    cxx = s * S / 2
    r = s * S * 0.34
    topy = s * S * 0.06
    d.ellipse((cxx - r, topy, cxx + r, topy + 2 * r), fill=color)
    d.polygon([(cxx - r * 0.82, topy + r * 1.12), (cxx + r * 0.82, topy + r * 1.12), (cxx, s * S * 0.96)], fill=color)
    hr = r * 0.40
    cyh = topy + r
    d.ellipse((cxx - hr, cyh - hr, cxx + hr, cyh + hr), fill=(255, 255, 255, 255))
    canvas.alpha_composite(tile.resize((s, s), Image.LANCZOS), (int(cx - s / 2), int(cy - s / 2)))


def _draw_eyebrow(canvas: Image.Image, x: int, y: int, label: str, h: int, accent: tuple[int, int, int]):
    d = ImageDraw.Draw(canvas, "RGBA")
    r = int(h * 0.30)
    cyc = y + h // 2
    d.ellipse((x, cyc - r, x + 2 * r, cyc + r), fill=accent)
    f = _load_font(FONT_PATH_DISPLAY_MED, int(h * 0.86))
    fb = d.textbbox((0, 0), "AG", font=f)
    _tracked_text(d, x + 2 * r + int(h * 0.5), cyc - (fb[3] - fb[1]) // 2 - fb[1], label.upper(), f, WARM_WHITE, max(2, int(h * 0.12)))


def _draw_date_chip(canvas: Image.Image, x: int, y: int, h: int, day: str, time: str, accent: tuple[int, int, int], primary: tuple[int, int, int]) -> int:
    """Calendar-style chip: an accent day cell + the time. Returns its right x."""
    d = ImageDraw.Draw(canvas, "RGBA")
    sq = h
    d.rounded_rectangle((x, y, x + sq, y + h), radius=max(8, h // 5), fill=accent)
    df = _fit_font_width(d, day, FONT_PATH_DISPLAY, int(sq * 0.74), int(h * 0.54), int(h * 0.26))
    db = d.textbbox((0, 0), day, font=df)
    d.text((x + (sq - (db[2] - db[0])) // 2 - db[0], y + (h - (db[3] - db[1])) // 2 - db[1]), day, font=df, fill=primary)
    tx = x + sq + int(h * 0.34)
    tf = _load_font(FONT_PATH_DISPLAY_MED, int(h * 0.56))
    tb = d.textbbox((0, 0), time, font=tf)
    d.text((tx, y + (h - (tb[3] - tb[1])) // 2 - tb[1]), time, font=tf, fill=WARM_WHITE)
    return tx + (tb[2] - tb[0])


def _draw_pin_row(canvas: Image.Image, x: int, y: int, h: int, text: str, accent: tuple[int, int, int]) -> int:
    d = ImageDraw.Draw(canvas, "RGBA")
    _icon_pin(canvas, x + int(h * 0.34), y + h // 2, int(h * 0.92), accent)
    tx = x + int(h * 0.92)
    f = _load_font(FONT_PATH_DISPLAY_MED, int(h * 0.66))
    fb = d.textbbox((0, 0), text, font=f)
    d.text((tx, y + (h - (fb[3] - fb[1])) // 2 - fb[1]), text, font=f, fill=WARM_WHITE)
    return tx + (fb[2] - fb[0])


def _draw_cta_pill(canvas: Image.Image, right_x: int, y: int, h: int, text: str, accent: tuple[int, int, int], primary: tuple[int, int, int]) -> int:
    """Right-aligned accent pill — the single bold call-to-action. Returns left x."""
    d = ImageDraw.Draw(canvas, "RGBA")
    text = text.upper()
    f = _fit_font_width(d, text, FONT_PATH_DISPLAY, int(right_x * 0.5), int(h * 0.46), int(h * 0.26))
    tb = d.textbbox((0, 0), text, font=f)
    padx = int(h * 0.55)
    pw = (tb[2] - tb[0]) + padx * 2
    x0 = right_x - pw
    d.rounded_rectangle((x0, y, x0 + pw, y + h), radius=h // 2, fill=accent)
    d.text((x0 + padx - tb[0], y + (h - (tb[3] - tb[1])) // 2 - tb[1]), text, font=f, fill=primary)
    return x0


def _draw_price_lockup(canvas: Image.Image, x: int, baseline_y: int, spec: PromotionSpec, accent: tuple[int, int, int], big_h: int) -> int:
    """Left-aligned hero price in accent: euros + superscript cents + currency,
    with an optional struck-through old price. Returns the top y of the price."""
    draw = ImageDraw.Draw(canvas)
    euros, cents, cur = _split_price(_offer_value(spec))
    ef = _load_font(FONT_PATH_DISPLAY_COMPRESSED, big_h)
    eb = draw.textbbox((0, 0), euros, font=ef)
    ew, eh = eb[2] - eb[0], eb[3] - eb[1]
    top = baseline_y - eh
    sh = max(2, big_h // 90)
    draw.text((x - eb[0] + sh, top - eb[1] + sh), euros, font=ef, fill=(0, 0, 0, 140))
    draw.text((x - eb[0], top - eb[1]), euros, font=ef, fill=accent)
    tail_x = x + ew + int(big_h * 0.05)
    cf = _load_font(FONT_PATH_DISPLAY_COMPRESSED, int(big_h * 0.5))
    if cents:
        cbb = draw.textbbox((0, 0), cents, font=cf)
        draw.text((tail_x - cbb[0], top - cbb[1]), cents, font=cf, fill=accent)
    curf = _load_font(FONT_PATH_DISPLAY_MED, int(big_h * 0.4))
    if cur:
        cu = draw.textbbox((0, 0), cur, font=curf)
        draw.text((tail_x - cu[0], baseline_y - (cu[3] - cu[1]) - cu[1]), cur, font=curf, fill=accent)
    if spec.old_price and not _is_event(spec):
        old = f"statt {spec.old_price}"
        of = _load_font(FONT_PATH_DISPLAY_MED, int(big_h * 0.20))
        ob = draw.textbbox((0, 0), old, font=of)
        ox, oy = x, top - (ob[3] - ob[1]) - int(big_h * 0.10)
        draw.text((ox - ob[0], oy - ob[1]), old, font=of, fill=WARM_WHITE)
        draw.line((ox, oy + (ob[3] - ob[1]) * 0.5, ox + (ob[2] - ob[0]), oy + (ob[3] - ob[1]) * 0.5), fill=RED, width=max(2, big_h // 36))
    return top


def _compose_event(canvas: Image.Image, spec: PromotionSpec, primary, accent, margin: int, safe_bottom: int, ratio: float):
    """Keep the hero image clean; carry the message in one premium content card."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)

    kicker = _event_kicker(spec)
    title = _display_title(spec).upper()
    kind = _event_copy_kind(spec)
    day, time_value = _event_date_parts(spec.validity)
    day_lbl = day if day and day != "TERMIN" else "TERMIN"
    time_lbl = time_value or "VOR ORT"
    price = (spec.price or "").strip()
    cta = price if price else ("Eintritt frei" if kind == "football" else "Aktion im Markt")
    place = _short_event_info(spec.origin)
    loc_text = "EDEKA Mühlenbein" + ("" if place in {"", "KASSEL", "IM MARKT"} else f" · {place.title()}")

    card_x0, card_x1 = margin, w - margin
    card_w = card_x1 - card_x0
    pad = int(card_w * 0.06)
    inner_w = card_w - 2 * pad

    eyebrow_h = int(h * 0.026)
    title_cap = int(h * 0.078)
    chip_h = int(h * 0.052)
    loc_h = int(h * 0.034)
    gap = int(h * 0.024)
    pad_v = int(h * 0.030)

    hf, hl, line_h, head_total, head_widest = _fit_headline(draw, title, inner_w, title_cap * 2, max_lines=2)

    content_h = eyebrow_h + int(gap * 0.6) + head_total + gap + chip_h + int(gap * 0.9) + loc_h
    card_h = content_h + pad_v * 2
    card_top = safe_bottom - card_h
    card_top = min(max(card_top, int(h * 0.40)), int(h * 0.62))

    radius = int(w * 0.030)
    _glass_panel(canvas, (card_x0, card_top, card_x1, safe_bottom), radius, accent, round_bottom=False)

    ix = card_x0 + pad
    iy = card_top + pad_v
    _draw_eyebrow(canvas, ix, iy, kicker, eyebrow_h, accent)
    iy += eyebrow_h + int(gap * 0.6)
    iy = _draw_headline(canvas, ix, iy, hf, hl, line_h, fill=(255, 255, 255))
    iy += gap
    _draw_date_chip(canvas, ix, iy, chip_h, day_lbl, time_lbl, accent, primary)
    _draw_cta_pill(canvas, card_x1 - pad, iy, chip_h, cta, accent, primary)
    iy += chip_h + int(gap * 0.9)
    _draw_pin_row(canvas, ix, iy, loc_h, loc_text, accent)


def _compose_product(canvas: Image.Image, spec: PromotionSpec, product: Image.Image | None, primary, accent, margin: int, safe_bottom: int, tall: bool, square: bool):
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    if square:
        x = int(w * 0.50)
        block_w = w - x - margin - int(w * 0.018)
    else:
        x = margin + int(w * 0.018)
        block_w = w - margin * 2 - int(w * 0.036)

    title = spec.product.upper()
    claim = _copy_clean(spec.claim or spec.origin or spec.category or "")
    kicker_h = int(h * (0.030 if not square else 0.028))
    head_max_h = int(h * (0.135 if not square else 0.125))
    big_price = int(h * (0.115 if not square else 0.105))
    claim_h = int(h * 0.030)
    validity_h = int(h * 0.024)
    gap = int(h * 0.020)

    hf, hl, line_h, head_total, head_widest = _fit_headline(draw, title, block_w, head_max_h, max_lines=2)
    cl: list[str] = []
    cl_h = 0
    claim_block = 0
    if claim:
        cf, cl = _fit_wrapped(draw, claim, FONT_PATH_DISPLAY_LIGHT, block_w, int(claim_h * 2.2), claim_h, int(claim_h * 0.55), max_lines=2, line_spacing=1.08)
        cl_h = _text_size(draw, "Ág", cf)[1]
        claim_block = int(cl_h * 1.08 * len(cl))
    old_block = int(big_price * 0.32) if (spec.old_price and not _is_event(spec)) else 0

    # --- bottom-anchored type stack (validity → price → claim → headline → kicker) ---
    bottom = safe_bottom - int(h * 0.035)
    validity = spec.validity.upper()
    vfit = _fit_font_width(draw, validity, FONT_PATH_DISPLAY_MED, block_w, validity_h, int(validity_h * 0.6))
    vb = draw.textbbox((0, 0), validity, font=vfit)
    draw.text((x - vb[0], bottom - (vb[3] - vb[1]) - vb[1]), validity, font=vfit, fill=_mix(WARM_WHITE, primary, 0.20))

    price_baseline = bottom - (vb[3] - vb[1]) - int(gap * 0.7)
    price_top = _draw_price_lockup(canvas, x, price_baseline, spec, accent, big_price)

    cur = price_top - old_block - int(gap * 0.9)
    if claim:
        cur -= claim_block
        cyy = cur
        for line in cl:
            lb = draw.textbbox((0, 0), line, font=cf)
            draw.text((x - lb[0], cyy - lb[1]), line, font=cf, fill=_mix(WARM_WHITE, primary, 0.06))
            cyy += int(cl_h * 1.08)
        cur -= int(gap * 0.7)

    cur -= head_total
    head_top = cur
    _draw_headline(canvas, x, head_top, hf, hl, line_h, fill=(255, 255, 255))

    kicker_block = int(kicker_h * 1.05)
    cur = head_top - int(gap * 0.5) - kicker_block
    _draw_kicker(canvas, x, cur, "Angebot", kicker_h, accent)
    block_top = cur

    # --- product hero, fitted strictly above the type block (no overlap) ---
    if product is not None:
        if square:
            _draw_cutout(canvas, product, int(w * 0.27), int(h * 0.46), (int(w * 0.44), int(h * 0.64)), angle=-1.5)
        else:
            avail_top = margin + int(h * 0.115)
            avail_bottom = block_top - int(h * 0.015)
            cy = (avail_top + avail_bottom) // 2
            box_h = max(int(h * 0.18), avail_bottom - avail_top)
            _draw_cutout(canvas, product, int(w * 0.52), cy, (int(w * 0.82), box_h), angle=-1.5)


def _layout_ai(canvas: Image.Image, spec: PromotionSpec, direction: CreativeDirection, fmt: FormatType, event_background: Path | None = None):
    """Editorial, photo-led AI poster — type lives on the artwork, one accent."""
    w, h = canvas.size
    ratio = h / w
    tall = ratio > 1.12
    square = 0.92 <= ratio <= 1.12
    is_event = _is_event(spec)
    primary, _accent_raw, theme, paper = _ai_palette(spec, direction)
    accent = _hex_to_rgb(BRAND_YELLOW)  # one disciplined marketing accent
    margin = int(w * 0.055)
    footer_h = int(h * 0.12)
    safe_bottom = h - footer_h

    product = None if is_event else _load_product_image(spec, (int(w * 0.86), int(h * 0.52)))

    if is_event and event_background:
        _grade_photo(canvas, event_background, primary)
    elif is_event:
        _graphic_backdrop(canvas, spec, primary, accent, theme)
    else:
        _product_backdrop(canvas, primary, theme)
        _draw_poster_frame(canvas, margin, (*WARM_WHITE, 55), safe_bottom)

    brand_h = int(h * (0.058 if not square else 0.07))
    _draw_brand_lockup(canvas, margin + int(w * 0.012), margin + int(h * 0.006), brand_h, accent, sub_color=WARM_WHITE, halo=True)

    if is_event:
        _compose_event(canvas, spec, primary, accent, margin, safe_bottom, ratio)
    else:
        _compose_product(canvas, spec, product, primary, accent, margin, safe_bottom, tall, square)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compose_promotion(
    spec: PromotionSpec,
    direction: CreativeDirection,
    format_type: FormatType,
    output_path: Path,
    scale: float = 1.0,
    event_background: Path | None = None,
) -> Path:
    fmt = EXPORT_FORMATS[format_type]
    # `scale` < 1 renders a smaller canvas for fast previews; the layout is
    # fully proportional so the result is identical, just lower resolution.
    cw = max(1, round(fmt.width * scale))
    ch = max(1, round(fmt.height * scale))
    canvas = Image.new("RGBA", (cw, ch), (255, 255, 255, 255))

    style = (getattr(spec, "style", None) or "edeka").lower()
    if style == "ai":
        _layout_ai(canvas, spec, direction, format_type, event_background=event_background)
    elif style == "luxe":
        _layout_luxe(canvas, spec, format_type)
    elif style == "editorial":
        _layout_editorial(canvas, spec, format_type)
    elif style == "colorblock":
        _layout_colorblock(canvas, spec, format_type)
    elif style == "lifestyle":
        _layout_lifestyle(canvas, spec, format_type)
    elif style == "magazine":
        _layout_magazine(canvas, spec, format_type)
    elif style == "retro":
        _layout_retro(canvas, spec, format_type)
    else:
        # EDEKA Style: bold Knaller layout, fixed brand colours.
        primary = _hex_to_rgb(BRAND_ANTHRACITE)
        secondary = _hex_to_rgb(BRAND_BLUE)
        accent = _hex_to_rgb(BRAND_YELLOW)
        cfg = _build_style_config(spec, primary, accent, "edeka", secondary=secondary)
        if format_type == FormatType.POST:
            _layout_post(canvas, spec, cfg)
        elif format_type == FormatType.STORY:
            _layout_story(canvas, spec, cfg)
        else:
            _layout_poster(canvas, spec, cfg)

    # Brand footer (adapted to the design) on every promotion.
    _draw_footer_banner(canvas, spec)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(str(output_path), quality=96, optimize=True)
    return output_path
