from app.schemas.promotion import PromotionSpec


def normalize_price(price: str) -> str:
    price = price.strip()
    if not price:
        return ""
    if not any(ch.isdigit() for ch in price):
        return price
    if not any(sym in price for sym in ["€", "$", "¥"]):
        price = f"{price} €"
    return price


def normalize_product_name(name: str) -> str:
    return name.strip().capitalize()


def validate_and_create_spec(data: dict) -> PromotionSpec:
    # Remove frontend-only flags not part of PromotionSpec
    data = {k: v for k, v in data.items() if k != "use_ai_planning"}
    campaign_kind = data.get("campaign_kind") or "product"
    if campaign_kind == "product" and "price" in data:
        data["price"] = normalize_price(data["price"])
    elif "price" in data:
        data["price"] = str(data["price"]).strip()
    if campaign_kind == "product" and "old_price" in data and data["old_price"]:
        data["old_price"] = normalize_price(data["old_price"])
    elif campaign_kind != "product":
        data["old_price"] = None
    if "product" in data:
        data["product"] = normalize_product_name(data["product"])
    if campaign_kind == "multi":
        items = [i for i in (data.get("items") or []) if str((i or {}).get("name", "")).strip()]
        if len(items) < 2:
            raise ValueError("Ein Wochenangebote-Plakat braucht mindestens 2 Angebote")
        for item in items[:6]:
            item["name"] = normalize_product_name(str(item["name"]))
            item["price"] = normalize_price(str(item.get("price") or ""))
            if item.get("old_price"):
                item["old_price"] = normalize_price(str(item["old_price"]))
        data["items"] = items[:6]
    else:
        data["items"] = []
    return PromotionSpec(**data)
