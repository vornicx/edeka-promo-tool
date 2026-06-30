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


def _event_scene_kind(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["wm", "world cup", "weltmeister", "fußball", "fussball", "football", "soccer", "europameister", " em "]):
        return "football"
    if any(k in t for k in ["schoko", "chocolate", "kakao", "praline"]):
        return "chocolate"
    if any(k in t for k in ["verkost", "tasting", "probier", "degust", "wein", "käse", "kaese"]):
        return "tasting"
    if any(k in t for k in ["sommer", "summer", "grill", "bbq", "garten"]):
        return "summer"
    return "generic"


_EVENT_SCENES = {
    "football": (
        "A lively outdoor public-viewing football party in front of a modern German neighbourhood "
        "supermarket at golden hour. A happy crowd of friends and families cheering, a big softly "
        "blurred screen in the background, warm string lights overhead, plain red-black-gold colour "
        "accents on scarves and cheeks, cold drinks and grilled snacks, festive yet premium energy."
    ),
    "chocolate": (
        "An elegant in-store chocolate tasting moment in a premium German supermarket. A wooden table "
        "with assorted fine chocolates and cocoa textures, warm inviting light, a few people savouring "
        "samples, rich brown and gold tones, artisanal and indulgent."
    ),
    "tasting": (
        "A refined in-store tasting event in a German supermarket. A counter with regional specialities, "
        "warm focused light, a friendly host offering samples to relaxed customers, authentic premium deli atmosphere."
    ),
    "summer": (
        "A warm summer market and grill event in front of a German supermarket. Bright natural daylight, "
        "fresh produce and a grill with smoke, relaxed people enjoying the day, fresh green and warm tones."
    ),
    "generic": (
        "A welcoming community event at a German neighbourhood supermarket. Friendly people, warm natural "
        "light and a festive but tasteful atmosphere that matches the occasion."
    ),
}


def _event_image_prompt(spec: PromotionSpec, direction: CreativeDirection) -> str:
    kind = _event_scene_kind(" ".join(filter(None, [spec.product, spec.event_description, spec.claim])))
    scene = _EVENT_SCENES.get(kind, _EVENT_SCENES["generic"])
    mood = (spec.event_description or spec.claim or "").strip()
    return (
        "Professional photorealistic advertising photograph — a real DSLR editorial scene, not a poster "
        "and not a graphic. "
        f"Scene: {scene} "
        + (f"Honour these real-world details in the scene (as visuals only, never as written words): {mood}. " if mood else "")
        + "Look: cinematic natural lighting, shallow depth of field, rich but realistic colour, polished "
        "retail-advertising composition, candid authentic people, premium yet approachable. "
        "Framing: place the main subjects in the upper and middle area and keep the lower third and the "
        "top-left corner calm and uncluttered, so graphics can be overlaid there afterwards. "
        # Hard constraint, stated forcefully and specifically because image models love to invent signage:
        "CRITICAL — THE IMAGE MUST CONTAIN ABSOLUTELY NO TEXT. No words, letters, numbers, captions, "
        "titles, headlines, event names, dates, price tags, menus, posters or banners with writing, "
        "chalkboards with writing, shop signs, store-name lettering, brand logos, sponsor logos, football "
        "team crests, tournament logos, QR codes or watermarks anywhere. Every sign, board, screen, banner "
        "or label must be blank, abstract or softly out of focus with no legible characters. Specifically do "
        "NOT render the words 'WM-PARTY', 'EDEKA', 'Mühlenbein', 'Grill station' or any date. "
        "Photography only: no cartoon, no illustration, no 3D lettering, no clipart, no stickers, no UI."
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
