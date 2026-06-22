"""User product library: uploaded product photos become reusable templates.

Photos are stored in the user's data directory (writable, persists across runs
and survives app updates) together with a JSON catalog. The composer resolves
these custom products the same way it resolves the bundled ones.
"""
from __future__ import annotations

import base64
import binascii
import io
import json
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

from app.config import settings

MAX_DIMENSION = 2000  # px on the longest side when storing
BG_TOLERANCE = 32     # colour distance to treat a pixel as background


def _user_dir() -> Path:
    # Reuse the same per-user data directory the rest of the app writes to.
    base = settings.output_dir.parent  # output_dir = <user_data>/output
    p = base / "product_photos"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_catalog_path() -> Path:
    return _user_dir().parent / "products.json"


def normalize(value: str | None) -> str:
    if not value:
        return ""
    clean = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return clean.lower().strip()


# ---------------------------------------------------------------------------
# Catalog persistence
# ---------------------------------------------------------------------------

def load_catalog() -> list[dict]:
    path = get_catalog_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_catalog(items: list[dict]) -> None:
    path = get_catalog_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")


def _keywords_for(name: str) -> list[str]:
    n = normalize(name)
    words = [w for w in n.replace("-", " ").split(" ") if len(w) > 2]
    return sorted(set([n, *words])) if n else []


# ---------------------------------------------------------------------------
# Image processing (background removal for plain/white backgrounds)
# ---------------------------------------------------------------------------

def _trim_alpha(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    return image.crop(bbox) if bbox else image


def _remove_background(img: Image.Image) -> Image.Image:
    """Make a plain (white/solid) background transparent.

    If the image already carries transparency it is kept as-is. Otherwise the
    background colour is sampled from the corners and pixels close to it become
    transparent. Works best for product photos on a plain/white backdrop;
    transparent PNGs always work perfectly.
    """
    img = img.convert("RGBA")
    alpha = img.getchannel("A")
    if alpha.getextrema()[0] < 250:
        return _trim_alpha(img)  # already has transparency

    rgb = img.convert("RGB")
    w, h = rgb.size
    corners = [
        rgb.getpixel((1, 1)),
        rgb.getpixel((w - 2, 1)),
        rgb.getpixel((1, h - 2)),
        rgb.getpixel((w - 2, h - 2)),
    ]
    bg = tuple(sum(c[i] for c in corners) // len(corners) for i in range(3))

    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, bg))
    r, g, b = diff.split()
    dist = ImageChops.lighter(ImageChops.lighter(r, g), b)  # max per-channel diff
    # foreground where distance exceeds tolerance
    mask = dist.point(lambda p: 255 if p > BG_TOLERANCE else 0)
    mask = mask.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(1))
    img.putalpha(mask)
    trimmed = _trim_alpha(img)
    # If removal nuked almost everything (busy/coloured background), keep the
    # original image rather than returning a near-empty cutout.
    if not trimmed.getbbox() or trimmed.width < w * 0.15 or trimmed.height < h * 0.15:
        return img
    return trimmed


def _decode_image(image_base64: str) -> Image.Image:
    raw = image_base64.split(",", 1)[1] if "," in image_base64[:64] else image_base64
    try:
        data = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Bilddaten konnten nicht gelesen werden") from exc
    try:
        return Image.open(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001 - PIL raises various errors
        raise ValueError("Ungültiges Bildformat") from exc


def process_and_store_image(image_base64: str, file_stem: str) -> str:
    img = _decode_image(image_base64)
    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
    processed = _remove_background(img)
    filename = f"{file_stem}.png"
    processed.save(str(_user_dir() / filename))
    return filename


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_product(name: str, category: str | None, image_base64: str) -> dict:
    name = (name or "").strip()
    if not name:
        raise ValueError("Der Produktname ist erforderlich")
    pid = uuid.uuid4().hex
    filename = process_and_store_image(image_base64, pid)
    entry = {
        "id": pid,
        "name": name,
        "category": (category or "").strip(),
        "keywords": _keywords_for(name),
        "file": filename,
        "created": datetime.now(timezone.utc).isoformat(),
    }
    catalog = load_catalog()
    catalog.insert(0, entry)
    save_catalog(catalog)
    return entry


def delete_product(product_id: str) -> bool:
    catalog = load_catalog()
    remaining = []
    removed = False
    for e in catalog:
        if e.get("id") == product_id:
            removed = True
            f = _user_dir() / e.get("file", "")
            if f.exists():
                try:
                    f.unlink()
                except OSError:
                    pass
        else:
            remaining.append(e)
    if removed:
        save_catalog(remaining)
    return removed


def get_product_file(product_id: str) -> Path | None:
    for e in load_catalog():
        if e.get("id") == product_id:
            p = _user_dir() / e.get("file", "")
            return p if p.exists() else None
    return None


def resolve_custom_asset(product: str, category: str | None) -> Path | None:
    """Return the uploaded photo whose name best matches the promotion, if any."""
    hay = normalize(f"{product} {category or ''}")
    if not hay:
        return None
    for e in load_catalog():  # most-recent first
        name_n = normalize(e.get("name"))
        keywords = e.get("keywords") or []
        if name_n and (name_n in hay or hay in name_n or any(k in hay for k in keywords)):
            p = _user_dir() / e.get("file", "")
            if p.exists():
                return p
    return None
