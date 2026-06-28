from __future__ import annotations

import base64
import logging
from pathlib import Path

import httpx

from app.config import settings
from app.schemas.promotion import CreativeDirection, FormatType, PromotionSpec
from app.user_settings import get_effective_ai_settings

logger = logging.getLogger(__name__)

IMAGE_MODEL_FALLBACKS = (
    "google/gemini-3.1-flash-image",
    "google/gemini-2.5-flash-image",
    "openai/gpt-image-1-mini",
)


def _event_image_prompt(spec: PromotionSpec, direction: CreativeDirection) -> str:
    components = []
    for item in getattr(direction, "event_components", []) or []:
        label = getattr(item, "label", "") or ""
        description = getattr(item, "description", "") or ""
        if label or description:
            components.append(f"{label}: {description}".strip(": "))
    component_text = "; ".join(components[:4]) or (spec.event_description or spec.claim or spec.product)

    title = spec.product.strip()
    description = (spec.event_description or spec.claim or "").strip()
    claim = (spec.claim or "").strip()
    return (
        "Create the main photorealistic promotional scene for a German EDEKA Mühlenbein event poster. "
        "Interpret the event briefing literally and visually. The image must show the event world, not generic abstract cards. "
        f"Event title written by the user: {title}. "
        f"Event description from the form cells: {description}. "
        f"Claim or mood from the form cells: {claim}. "
        f"Date/time context: {spec.validity}. Location context: {spec.origin or 'EDEKA Mühlenbein Kassel'}. "
        f"Creative direction: {direction.intent}. Components to include as visual cues: {component_text}. "
        "If the title is WM Party, World Cup Party, Fußball Party, or similar: show a realistic supermarket celebration scene "
        "with happy people/fans celebrating, football/soccer party atmosphere, tasteful flags/garlands, snacks, drinks, "
        "green pitch-inspired lighting and big-screen viewing energy, but no official FIFA/World Cup logos or team crests. "
        "If the title is Chocolate Party or Schoko Party: show a premium chocolate tasting/event scene with chocolates, "
        "cocoa textures, dessert table, warm lighting, people enjoying the tasting if appropriate. "
        "For any other event: create a realistic scene with the people, props, food, decorations, lighting and atmosphere "
        "that naturally match the written event. "
        "Use professional retail advertising photography, realistic people when relevant, cinematic supermarket lighting, "
        "clear focal point, polished composition, premium but approachable. "
        "Do not add readable text, letters, numbers, labels, posters, price tags, logos, QR codes, fake signage, or watermark. "
        "Avoid cartoon, vector illustration, childish icons, flat clipart, stickers and UI components. "
        "Leave clean negative space for overlaid German headline, event information and QR footer."
    )


def _aspect_ratio(fmt: FormatType) -> str:
    if fmt == FormatType.STORY:
        return "9:16"
    if fmt == FormatType.POST:
        return "1:1"
    return "3:4"


def _model_payload(model: str, prompt: str, fmt: FormatType) -> dict[str, str | int]:
    payload: dict[str, str | int] = {
        "model": model,
        "prompt": prompt,
        "n": 1,
    }
    if model.startswith("google/gemini"):
        payload["aspect_ratio"] = _aspect_ratio(fmt)
        payload["resolution"] = "1K"
    elif model.startswith("openai/"):
        payload["quality"] = "low"
        payload["background"] = "opaque"
    return payload


async def generate_event_background(
    spec: PromotionSpec,
    direction: CreativeDirection,
    fmt: FormatType,
    output_dir: Path,
) -> Path | None:
    ai = get_effective_ai_settings()
    if not ai.api_key or not ai.enabled:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "event_background.png"
    prompt = _event_image_prompt(spec, direction)
    requested_model = ai.image_model or settings.openrouter_image_model
    models = list(dict.fromkeys([requested_model, *IMAGE_MODEL_FALLBACKS]))
    headers = {
        "Authorization": f"Bearer {ai.api_key}",
        "Content-Type": "application/json",
    }

    for model in models:
        payload = _model_payload(model, prompt, fmt)
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(f"{settings.openrouter_base_url.rstrip('/')}/images", headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
            image_data = result["data"][0]["b64_json"]
            output_path.write_bytes(base64.b64decode(image_data))
            logger.info("KI-Event-Hintergrund generiert mit %s", model)
            return output_path
        except Exception as exc:  # noqa: BLE001
            logger.warning("KI-Event-Hintergrund konnte mit %s nicht generiert werden: %s", model, exc)
    return None
