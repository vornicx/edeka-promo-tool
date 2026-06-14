from PIL import Image, ImageDraw
from pathlib import Path
from app.assets.brand import SECTION_GRADIENTS
from app.config import settings


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def create_gradient_background(
    width: int,
    height: int,
    color_start: str,
    color_end: str,
    direction: str = "vertical",
) -> Image.Image:
    start_rgb = hex_to_rgb(color_start)
    end_rgb = hex_to_rgb(color_end)
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    for i in range(height if direction == "vertical" else width):
        ratio = i / (height if direction == "vertical" else width)
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
        if direction == "vertical":
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        else:
            draw.line([(i, 0), (i, height)], fill=(r, g, b))

    return img


def get_background_for_section(section: str, width: int, height: int) -> Image.Image:
    colors = SECTION_GRADIENTS.get(section, SECTION_GRADIENTS["default"])
    return create_gradient_background(width, height, colors[0], colors[1])


def ensure_backgrounds_exist():
    bg_dir = settings.backgrounds_dir
    for section, colors in SECTION_GRADIENTS.items():
        bg_path = bg_dir / f"{section}_1080x1080.png"
        if not bg_path.exists():
            img = create_gradient_background(1080, 1080, colors[0], colors[1])
            img.save(bg_path, quality=95)
