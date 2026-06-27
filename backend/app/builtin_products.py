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
    {"key": "pointed_peppers", "name": "Bio Spitzpaprika rot", "category": "Gemüse"},
    {"key": "cheese_slices", "name": "Milram Käsescheiben", "category": "Käse"},
    {"key": "soft_cheese", "name": "Cambozola / Rougette", "category": "Bedientheke"},
    {"key": "ice_cream_tub", "name": "Mövenpick Eis", "category": "Tiefkühl"},
    {"key": "icecream_bars", "name": "Magnum Multipack Eis", "category": "Tiefkühl"},
    {"key": "pizza", "name": "Wagner Steinofen Pizza", "category": "Tiefkühl"},
    {"key": "juice_bottle", "name": "Saft oder Nektar", "category": "Getränke"},
    {"key": "milk_drink", "name": "Müllermilch", "category": "Milchprodukte"},
    {"key": "pasta", "name": "Barilla Pasta", "category": "Nudeln & Sauce"},
    {"key": "pesto_sauce", "name": "Barilla Pesto / Pastasauce", "category": "Nudeln & Sauce"},
]


def builtin_file(key: str) -> Path | None:
    path = ASSET_DIR / f"{key}.png"
    return path if path.exists() else None


def list_builtin() -> list[dict]:
    return [p for p in BUILTIN_PRODUCTS if builtin_file(p["key"]) is not None]
