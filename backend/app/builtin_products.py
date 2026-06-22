"""Catalog of the bundled product motifs (German labels) for the picker."""
from __future__ import annotations

from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parent / "assets" / "product_photos"

# key -> (German label, category)
BUILTIN_PRODUCTS: list[dict] = [
    {"key": "strawberries", "name": "Erdbeeren", "category": "Obst"},
    {"key": "apples", "name": "Äpfel", "category": "Obst"},
    {"key": "bananas", "name": "Bananen", "category": "Obst"},
    {"key": "oranges", "name": "Orangen", "category": "Obst"},
    {"key": "grapes", "name": "Trauben", "category": "Obst"},
    {"key": "mixed_fruit", "name": "Obst gemischt", "category": "Obst"},
    {"key": "tomatoes", "name": "Tomaten", "category": "Gemüse"},
    {"key": "cucumbers", "name": "Gurken", "category": "Gemüse"},
    {"key": "carrots", "name": "Karotten", "category": "Gemüse"},
    {"key": "lettuce", "name": "Salat", "category": "Gemüse"},
    {"key": "peppers", "name": "Paprika", "category": "Gemüse"},
    {"key": "mixed_vegetables", "name": "Gemüse gemischt", "category": "Gemüse"},
]


def builtin_file(key: str) -> Path | None:
    path = ASSET_DIR / f"{key}.png"
    return path if path.exists() else None


def list_builtin() -> list[dict]:
    return [p for p in BUILTIN_PRODUCTS if builtin_file(p["key"]) is not None]
