from app.adapters.base import AIAdapter
from app.schemas.promotion import PromotionSpec, EnrichmentSpec


SYSTEM_PROMPT = """Actúa como analista de marketing retail para EDEKA Mühlenbein en Kassel.
Tu tarea es analizar una ficha de producto y devolver un enriquecimiento semántico estructurado.

Contexto de marca:
- Mercado local EDEKA Mühlenbein en Kassel
- Identidad diferencial, cercana, innovadora
- Posible uso del personaje Waschbér (mapache) como elemento de marca

Devuelve SOLO JSON válido con esta estructura:
{
  "campaign_type": "fresh_product_offer | daily_special | seasonal_campaign | brand_story",
  "product_family": "fruta | verdura | panaderia | lacteos | carnes | pescados | bebidas | limpieza | hogar | otros",
  "seasonality": "spring_summer | autumn_winter | all_year | holiday_specific",
  "communication_style": "close_and_fresh | elegant_restrained | bold_direct | warm_community",
  "price_priority": "high | medium | low",
  "visual_energy": "low | medium_low | medium | medium_high | high",
  "brand_mode": "muehlenbein_local | edeka_standard | waschbaer_featured",
  "waschbaer_presence": "none | subtle | graphic_accent | featured"
}"""


def build_user_prompt(spec: PromotionSpec) -> str:
    parts = [f"Producto: {spec.product}"]
    if spec.category:
        parts.append(f"Categoría: {spec.category}")
    parts.append(f"Precio: {spec.price}")
    if spec.old_price:
        parts.append(f"Precio anterior: {spec.old_price}")
    parts.append(f"Vigencia: {spec.validity}")
    if spec.origin:
        parts.append(f"Origen: {spec.origin}")
    if spec.claim:
        parts.append(f"Claim: {spec.claim}")
    parts.append(f"Tono: {spec.tone.value}")
    parts.append(f"Nivel de diferenciación: {spec.differentiation_level.value}")
    return "\n".join(parts)


async def enrich_promotion(
    ai: AIAdapter, spec: PromotionSpec
) -> EnrichmentSpec:
    user_prompt = build_user_prompt(spec)
    result = await ai.chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.5,
        max_tokens=800,
    )
    return EnrichmentSpec(**result)
