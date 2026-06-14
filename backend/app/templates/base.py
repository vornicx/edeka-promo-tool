from PIL import Image, ImageDraw, ImageFont
from abc import ABC, abstractmethod
from pathlib import Path
from app.assets.brand import (
    BRAND_BLUE,
    BRAND_YELLOW,
    BRAND_WHITE,
    BRAND_BLACK,
    FONT_PATH_REGULAR,
    FONT_PATH_BOLD,
    FONT_PATH_EXTRABOLD,
    WASCHBAER_LOGO_PATH,
)


class BaseTemplate(ABC):
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.canvas: Image.Image | None = None
        self.draw: ImageDraw.ImageDraw | None = None

    @abstractmethod
    def create_layout(self, background: Image.Image) -> Image.Image:
        pass

    def _load_font(self, path: str, size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            return ImageFont.load_default()

    def _draw_price_block(
        self,
        price: str,
        old_price: str | None = None,
        x: int = 0,
        y: int = 0,
    ):
        price_font = self._load_font(FONT_PATH_EXTRABOLD, self.width // 6)
        self.draw.text(
            (x, y),
            price,
            fill=BRAND_YELLOW,
            font=price_font,
            stroke_width=2,
            stroke_fill=BRAND_BLACK,
        )
        if old_price:
            old_font = self._load_font(FONT_PATH_REGULAR, self.width // 14)
            bbox = self.draw.textbbox((0, 0), old_price, font=old_font)
            text_width = bbox[2] - bbox[0]
            self.draw.text(
                (x + (self.width // 6 - text_width) // 2, y + self.width // 7),
                old_price,
                fill="#999999",
                font=old_font,
            )
            line_y = y + self.width // 7 + old_font.size // 2
            self.draw.line(
                [
                    (x + 5, line_y),
                    (x + text_width + 5, line_y),
                ],
                fill="#999999",
                width=3,
            )

    def _draw_product_name(self, name: str, x: int = 0, y: int = 0):
        font = self._load_font(FONT_PATH_BOLD, self.width // 10)
        self.draw.text((x, y), name.upper(), fill=BRAND_WHITE, font=font)

    def _draw_claim(self, claim: str, x: int = 0, y: int = 0):
        font = self._load_font(FONT_PATH_REGULAR, self.width // 16)
        self.draw.text((x, y), claim, fill=BRAND_WHITE, font=font)

    def _draw_validity(self, validity: str, x: int = 0, y: int = 0):
        font = self._load_font(FONT_PATH_BOLD, self.width // 18)
        text = f"⚡ {validity.upper()}"
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        box_padding = 20
        self.draw.rounded_rectangle(
            [x, y, x + text_w + box_padding * 2, y + font.size + box_padding],
            radius=10,
            fill=BRAND_YELLOW,
        )
        self.draw.text(
            (x + box_padding, y + box_padding // 2),
            text,
            fill=BRAND_BLACK,
            font=font,
        )

    def _draw_price_band(self, y: int, height: int):
        self.draw.rectangle(
            [0, y, self.width, y + height],
            fill=(*BRAND_BLUE, 200),
        )

    def _draw_washbaer(self, position: str = "bottom_right", scale: float = 0.15):
        if not WASCHBAER_LOGO_PATH.exists():
            return
        logo = Image.open(WASCHBAER_LOGO_PATH).convert("RGBA")
        logo_size = int(self.width * scale)
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        positions = {
            "bottom_right": (self.width - logo_size - 20, self.height - logo_size - 20),
            "bottom_left": (20, self.height - logo_size - 20),
            "top_right": (self.width - logo_size - 20, 20),
            "top_left": (20, 20),
        }
        pos = positions.get(position, positions["bottom_right"])
        self.canvas.paste(logo, pos, logo)

    def _draw_brand_bar(self, y: int):
        bar_height = self.height // 20
        self.draw.rectangle(
            [0, y, self.width, y + bar_height],
            fill=BRAND_BLUE,
        )
        font = self._load_font(FONT_PATH_BOLD, bar_height - 10)
        self.draw.text(
            (20, y + 5),
            "EDEKA MÜHLENBEIN",
            fill=BRAND_WHITE,
            font=font,
        )
