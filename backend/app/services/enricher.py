from app.adapters.base import AIAdapter
from app.schemas.promotion import PromotionSpec, EnrichmentSpec


SYSTEM_PROMPT = """Du bist Retail-Marketing-Analyst fuer EDEKA Muehlenbein in Kassel.
Deine Aufgabe ist es, ein Produktbriefing zu analysieren und eine strukturierte semantische Einordnung zurueckzugeben.

Markenkontext:
- Lokaler EDEKA Muehlenbein Markt in Kassel
- Nahbare, moderne und eigenstaendige Identitaet
- Hochwertige, kommerzielle Promotionen fuer den lokalen Markt

Gib nur gueltiges JSON mit dieser Struktur zurueck:
{
  "campaign_type": "fresh_product_offer | daily_special | seasonal_campaign | brand_story",
  "product_family": "fruit | vegetable | bakery | dairy | meat | fish | drinks | cleaning | household | other",
  "seasonality": "spring_summer | autumn_winter | all_year | holiday_specific",
  "communication_style": "close_and_fresh | elegant_restrained | bold_direct | warm_community",
  "price_priority": "high | medium | low",
  "visual_energy": "low | medium_low | medium | medium_high | high",
  "brand_mode": "muehlenbein_local | edeka_standard | waschbaer_featured",
  "waschbaer_presence": "none | subtle | graphic_accent | featured"
}"""


def build_user_prompt(spec: PromotionSpec) -> str:
    parts = [f"Produkt: {spec.product}"]
    if spec.category:
        parts.append(f"Kategorie: {spec.category}")
    parts.append(f"Preis: {spec.price}")
    if spec.old_price:
        parts.append(f"Alter Preis: {spec.old_price}")
    parts.append(f"Aktionszeitraum: {spec.validity}")
    if spec.origin:
        parts.append(f"Herkunft: {spec.origin}")
    if spec.claim:
        parts.append(f"Claim: {spec.claim}")
    parts.append(f"Tonalitaet: {spec.tone.value}")
    parts.append(f"Differenzierungsgrad: {spec.differentiation_level.value}")
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
