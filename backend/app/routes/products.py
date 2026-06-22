from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app import builtin_products, product_library

router = APIRouter(prefix="/api/products", tags=["products"])


class MotifOut(BaseModel):
    value: str  # "builtin:<key>" or "custom:<id>"
    name: str
    category: str = ""
    image_url: str
    source: str  # "builtin" | "custom"


class ProductOut(BaseModel):
    id: str
    name: str
    category: str = ""
    image_url: str
    created: str = ""


class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1)
    category: Optional[str] = None
    image_base64: str = Field(..., min_length=8, description="PNG/JPG als Base64 (optional data-URL)")


def _to_out(entry: dict) -> ProductOut:
    return ProductOut(
        id=entry["id"],
        name=entry.get("name", ""),
        category=entry.get("category", ""),
        image_url=f"/api/products/{entry['id']}/image",
        created=entry.get("created", ""),
    )


@router.get("")
async def list_products() -> list[ProductOut]:
    return [_to_out(e) for e in product_library.load_catalog()]


@router.get("/catalog")
async def motif_catalog() -> list[MotifOut]:
    """All selectable motifs: bundled ones first, then the user's own photos."""
    motifs: list[MotifOut] = [
        MotifOut(
            value=f"builtin:{p['key']}",
            name=p["name"],
            category=p["category"],
            image_url=f"/api/products/builtin/{p['key']}/image",
            source="builtin",
        )
        for p in builtin_products.list_builtin()
    ]
    motifs += [
        MotifOut(
            value=f"custom:{e['id']}",
            name=e.get("name", ""),
            category=e.get("category", ""),
            image_url=f"/api/products/{e['id']}/image",
            source="custom",
        )
        for e in product_library.load_catalog()
    ]
    return motifs


@router.get("/builtin/{key}/image")
async def builtin_image(key: str):
    path = builtin_products.builtin_file(key)
    if not path:
        raise HTTPException(status_code=404, detail="Motiv nicht gefunden")
    return FileResponse(str(path), media_type="image/png")


@router.post("")
async def create_product(request: CreateProductRequest) -> ProductOut:
    try:
        entry = product_library.add_product(request.name, request.category, request.image_base64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _to_out(entry)


@router.delete("/{product_id}")
async def remove_product(product_id: str):
    if not product_library.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    return {"status": "ok"}


@router.get("/{product_id}/image")
async def product_image(product_id: str):
    path = product_library.get_product_file(product_id)
    if not path:
        raise HTTPException(status_code=404, detail="Produktbild nicht gefunden")
    return FileResponse(str(path), media_type="image/png")
