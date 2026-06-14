from app.schemas.promotion import PromotionSpec


def normalize_price(price: str) -> str:
    price = price.strip()
    if not any(sym in price for sym in ["€", "$", "¥"]):
        price = f"{price} €"
    return price


def normalize_product_name(name: str) -> str:
    return name.strip().capitalize()


def validate_and_create_spec(data: dict) -> PromotionSpec:
    if "price" in data:
        data["price"] = normalize_price(data["price"])
    if "old_price" in data and data["old_price"]:
        data["old_price"] = normalize_price(data["old_price"])
    if "product" in data:
        data["product"] = normalize_product_name(data["product"])
    return PromotionSpec(**data)
