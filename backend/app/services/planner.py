from __future__ import annotations

from app.adapters.base import AIAdapter
from app.schemas.promotion import CreativeDirection, EnrichmentSpec, PromotionSpec


SYSTEM_PROMPT = """Du bist Senior Retail-Stratege fuer EDEKA Muehlenbein in Kassel.
Erzeuge einen kompakten Plan fuer eine Lebensmittel-Promotion: semantische Einordnung und 3 visuelle Richtungen.

Prioritaeten:
- Kommerziell klar, hochwertig und direkt umsetzbar.
- Niedrige Kosten: kurzes JSON, keine Erklaerungen.
- Professionelles Design, lesbar fuer Markt und Social Media.
- Preis, Produkt und Aktionszeitraum sind die Haupt-Hierarchie.

Antworte NUR mit gueltigem JSON:
{
  "enrichment": {
    "campaign_type": "fresh_product_offer | daily_special | seasonal_campaign | brand_story",
    "product_family": "fruta | verdura | panaderia | lacteos | carnes | pescados | bebidas | limpieza | hogar | otros",
    "seasonality": "spring_summer | autumn_winter | all_year | holiday_specific",
    "communication_style": "close_and_fresh | elegant_restrained | bold_direct | warm_community",
    "price_priority": "high | medium | low",
    "visual_energy": "low | medium_low | medium | medium_high | high",
    "brand_mode": "muehlenbein_local | edeka_standard | waschbaer_featured",
    "waschbaer_presence": "none | subtle | graphic_accent | featured"
  },
  "directions": [
    {
      "name": "kurzer_name",
      "intent": "kurze visuelle Absicht auf Deutsch",
      "composition": "kurze, umsetzbare Komposition auf Deutsch",
      "palette": ["#003B79", "#FFD500", "#FFFFFF"],
      "text_safe_area": "top_left | top_right | bottom_left | bottom_right | center",
      "boldness": "low | medium | high",
      "waschbaer_presence": "none | subtle | graphic_accent | featured"
    }
  ]
}

Erzeuge genau 3 Richtungen. Nutze gueltige Hex-Farben."""


def _product_family(spec: PromotionSpec) -> str:
    category = (spec.category or "").strip().lower()
    product = spec.product.lower()
    if category:
        return category
    keywords = {
        "fruta": ["fresa", "manzana", "naranja", "uva", "pera", "platano"],
        "verdura": ["tomate", "lechuga", "pepino", "zanahoria", "patata"],
        "panaderia": ["pan", "croissant", "bolleria", "baguette"],
        "lacteos": ["leche", "queso", "yogur", "mantequilla"],
        "carnes": ["pollo", "ternera", "cerdo", "jamon"],
        "pescados": ["salmon", "atun", "bacalao", "merluza"],
        "bebidas": ["agua", "zumo", "vino", "cerveza", "refresco"],
    }
    for family, terms in keywords.items():
        if any(term in product for term in terms):
            return family
    return "otros"


def _energy(spec: PromotionSpec) -> str:
    if spec.differentiation_level.value == "alto":
        return "high"
    if spec.differentiation_level.value == "bajo":
        return "medium_low"
    return "medium"


def _style(spec: PromotionSpec) -> str:
    if spec.tone.value == "premium":
        return "elegant_restrained"
    if spec.tone.value == "atrevido":
        return "bold_direct"
    if spec.tone.value == "local":
        return "warm_community"
    return "close_and_fresh"


def build_local_plan(spec: PromotionSpec) -> tuple[EnrichmentSpec, list[CreativeDirection]]:
    family = _product_family(spec)
    energy = _energy(spec)
    enrichment = EnrichmentSpec(
        campaign_type="fresh_product_offer" if family in {"fruta", "verdura"} else "daily_special",
        product_family=family,
        seasonality="all_year",
        communication_style=_style(spec),
        price_priority="high",
        visual_energy=energy,
        brand_mode="muehlenbein_local",
        waschbaer_presence="none",
    )

    product = spec.product
    price_area = "top_right" if spec.format.value == "story" else "bottom_right"
    directions = [
        CreativeDirection(
            name="Klarer Abverkauf",
            intent=f"{product}, Preis und Aktionszeitraum sofort erfassbar machen.",
            composition="Grosses Produktbild auf ruhiger Flaeche, Preis als starke Karte und kurzer Claim als Abschluss.",
            palette=["#003B79", "#FFD500", "#FFFFFF", "#E7F0FA"],
            text_safe_area=price_area,
            boldness="medium",
            waschbaer_presence="none",
        ),
        CreativeDirection(
            name="Frische vom Markt",
            intent="Nahe, frische Marktqualitaet zeigen und trotzdem klar verkaufen.",
            composition="Realistisches Produktbild im Fokus, lokale Anmutung und klare Preiszone im unteren Bereich.",
            palette=["#0B6E4F", "#FFD500", "#F7FAF7", "#003B79"],
            text_safe_area="bottom_left",
            boldness="medium",
            waschbaer_presence="none",
        ),
        CreativeDirection(
            name="Preis im Fokus",
            intent="Die Aktion in weniger als zwei Sekunden verstaendlich machen.",
            composition="Sehr praesenter Preis, reales Produkt mit Tiefe und kurzer Dringlichkeits-Hinweis.",
            palette=["#003B79", "#FFD500", "#D71920", "#FFFFFF"],
            text_safe_area="top_left",
            boldness="high" if spec.differentiation_level.value == "alto" else "medium",
            waschbaer_presence="none",
        ),
    ]
    return enrichment, directions


def _build_user_prompt(spec: PromotionSpec) -> str:
    lines = [
        f"Produkt: {spec.product}",
        f"Kategorie: {spec.category or 'nicht angegeben'}",
        f"Preis: {spec.price}",
        f"Statt-Preis: {spec.old_price or 'nicht angegeben'}",
        f"Aktionszeitraum: {spec.validity}",
        f"Herkunft: {spec.origin or 'nicht angegeben'}",
        f"Claim: {spec.claim or 'nicht angegeben'}",
        f"Format: {spec.format.value}",
        f"Tonalitaet: {spec.tone.value}",
        f"Kreativniveau: {spec.differentiation_level.value}",
    ]
    return "\n".join(lines)


async def generate_ai_plan(
    ai: AIAdapter, spec: PromotionSpec
) -> tuple[EnrichmentSpec, list[CreativeDirection]]:
    result = await ai.chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_build_user_prompt(spec),
        temperature=0.45,
        max_tokens=1100,
    )
    enrichment = EnrichmentSpec(**result["enrichment"])
    directions = [CreativeDirection(**item) for item in result["directions"][:3]]
    if len(directions) < 3:
        _, fallback = build_local_plan(spec)
        directions = (directions + fallback)[:3]
    return enrichment, directions
