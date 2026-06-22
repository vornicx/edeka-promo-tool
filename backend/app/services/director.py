from app.adapters.base import AIAdapter
from app.schemas.promotion import (
    PromotionSpec,
    EnrichmentSpec,
    CreativeDirection,
    CreativeDirectionsResponse,
)


SYSTEM_PROMPT = """Du bist Kreativdirektor fuer Food-Retail-Promotionen von EDEKA Muehlenbein.
Deine Aufgabe ist es, ein Handelsbriefing in bis zu 3 unterschiedliche, markenkonforme visuelle Richtungen zu verwandeln.

Markenkontext:
- Lokaler EDEKA Muehlenbein Markt in Kassel
- Nahbare, moderne und eigenstaendige Identitaet
- Die Umsetzung muss kommerziell, hochwertig und gut lesbar sein

Vorgaben:
- Keine langen Copytexte erzeugen
- Visuell Platz fuer Preis und Produkt lassen
- Jede Richtung muss klar unterscheidbar sein
- Farben im Hexformat (#XXXXXX)
- Nur gueltiges JSON zurueckgeben

Erforderliche Struktur:
{
  "directions": [
    {
      "name": "kurzer_name",
      "intent": "Beschreibung der visuellen Absicht",
      "composition": "Beschreibung der Komposition",
      "palette": ["#color1", "#color2", "#color3"],
      "text_safe_area": "top_left | top_right | bottom_left | bottom_right | center",
      "boldness": "low | medium | high",
      "waschbaer_presence": "none | subtle | graphic_accent | featured"
    }
  ]
}

Erzeuge genau 3 unterschiedliche Richtungen."""


def build_user_prompt(spec: PromotionSpec, enrichment: EnrichmentSpec) -> str:
    parts = [
        f"Produkt: {spec.product}",
        f"Preis: {spec.price}",
        f"Aktionszeitraum: {spec.validity}",
    ]
    if spec.claim:
        parts.append(f"Claim: {spec.claim}")
    if spec.origin:
        parts.append(f"Herkunft: {spec.origin}")
    parts.append(f"Format: {spec.format.value}")
    parts.append(f"Gewuenschte Tonalitaet: {spec.tone.value}")
    parts.append(f"Kampagnentyp: {enrichment.campaign_type}")
    parts.append(f"Produktfamilie: {enrichment.product_family}")
    parts.append(f"Stil: {enrichment.communication_style}")
    parts.append(f"Visuelle Energie: {enrichment.visual_energy}")
    parts.append(f"Preisprioritaet: {enrichment.price_priority}")
    parts.append(f"Waschbaer-Praesenz: {enrichment.waschbaer_presence}")
    return "\n".join(parts)


async def generate_directions(
    ai: AIAdapter, spec: PromotionSpec, enrichment: EnrichmentSpec
) -> list[CreativeDirection]:
    user_prompt = build_user_prompt(spec, enrichment)
    result = await ai.chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.8,
        max_tokens=1500,
    )
    response = CreativeDirectionsResponse(**result)
    return response.directions
