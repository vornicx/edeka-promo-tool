from app.adapters.base import AIAdapter
from app.schemas.promotion import (
    PromotionSpec,
    EnrichmentSpec,
    CreativeDirection,
    CreativeDirectionsResponse,
)


SYSTEM_PROMPT = """Actúa como director creativo para promociones de retail alimentario de EDEKA Mühlenbein.
Tu tarea es convertir una ficha comercial en hasta 3 direcciones visuales distintas pero coherentes con la marca.

Contexto de marca:
- Mercado local EDEKA Mühlenbein en Kassel
- Identidad diferencial, cercana, innovadora
- Posibilidad de guiño Waschbér (mapache)
- La pieza debe ser comercial y legible

Restricciones:
- No generes copy largo
- Deja espacio visual para precio y producto
- Cada dirección debe ser visualmente distinta
- Colores en formato hex (#XXXXXX)
- Devuelve SOLO JSON válido

Estructura requerida:
{
  "directions": [
    {
      "name": "nombre_corto",
      "intent": "descripción de la intención visual",
      "composition": "descripción de la composición",
      "palette": ["#color1", "#color2", "#color3"],
      "text_safe_area": "top_left | top_right | bottom_left | bottom_right | center",
      "boldness": "low | medium | high",
      "waschbaer_presence": "none | subtle | graphic_accent | featured"
    }
  ]
}

Genera exactamente 3 direcciones distintas."""


def build_user_prompt(spec: PromotionSpec, enrichment: EnrichmentSpec) -> str:
    parts = [
        f"Producto: {spec.product}",
        f"Precio: {spec.price}",
        f"Vigencia: {spec.validity}",
    ]
    if spec.claim:
        parts.append(f"Claim: {spec.claim}")
    if spec.origin:
        parts.append(f"Origen: {spec.origin}")
    parts.append(f"Formato: {spec.format.value}")
    parts.append(f"Tono solicitado: {spec.tone.value}")
    parts.append(f"Tipo de campaña: {enrichment.campaign_type}")
    parts.append(f"Familia: {enrichment.product_family}")
    parts.append(f"Estilo: {enrichment.communication_style}")
    parts.append(f"Energía visual: {enrichment.visual_energy}")
    parts.append(f"Prioridad precio: {enrichment.price_priority}")
    parts.append(f"Presencia Waschbär: {enrichment.waschbaer_presence}")
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
