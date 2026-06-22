from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app import product_library

router = APIRouter(prefix="/api/products", tags=["products"])


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
