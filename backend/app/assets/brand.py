from pathlib import Path

BRAND_BLUE = "#004C96"
BRAND_YELLOW = "#FFD600"
BRAND_WHITE = "#FFFFFF"
BRAND_BLACK = "#1A1A1A"
BRAND_LIGHT_GRAY = "#F5F5F5"
BRAND_DARK_GRAY = "#333333"

_FONTS_DIR = Path(__file__).parent / "fonts"
_SYSTEM_FONTS_DIR = Path("/usr/share/fonts/truetype/open-sans")


def _resolve_font(name: str) -> str:
    bundled = _FONTS_DIR / name
    if bundled.exists():
        return str(bundled)
    fallback = _SYSTEM_FONTS_DIR / name
    if fallback.exists():
        return str(fallback)
    return str(bundled)


FONT_PATH_REGULAR = _resolve_font("OpenSans-Regular.ttf")
FONT_PATH_BOLD = _resolve_font("OpenSans-Bold.ttf")
FONT_PATH_SEMIBOLD = _resolve_font("OpenSans-Semibold.ttf")
FONT_PATH_EXTRABOLD = _resolve_font("OpenSans-ExtraBold.ttf")

WASCHBAER_LOGO_PATH = Path(__file__).parent / "waschbaer_logo.png"

SECTION_GRADIENTS: dict[str, tuple[str, str]] = {
    "fruta_fresca": ("#4CAF50", "#C8E6C9"),
    "panaderia": ("#FF8F00", "#FFE0B2"),
    "lacteos": ("#42A5F5", "#E3F2FD"),
    "carnes": ("#C62828", "#FFCDD2"),
    "bebidas": ("#1565C0", "#BBDEFB"),
    "limpieza": ("#00ACC1", "#E0F7FA"),
    "default": ("#004C96", "#E3F2FD"),
}

TONE_OVERRIDES: dict[str, dict] = {
    "fresco": {"energy": "medium_high", "style": "close_and_fresh"},
    "premium": {"energy": "medium_low", "style": "elegant_restrained"},
    "atrevido": {"energy": "high", "style": "bold_direct"},
    "local": {"energy": "medium", "style": "warm_community"},
}
