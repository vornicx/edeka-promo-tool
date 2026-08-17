import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

FREE_FALLBACK_MODELS = [
    "openrouter/free",                        # auto-selects best free model
    "google/gemma-4-31b-it:free",            # best free vision
    "nvidia/nemotron-3-super-120b-a12b:free", # best free text
]

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-2.5-flash-lite"
DEFAULT_IMAGE_MODEL = "google/gemini-3.1-flash-image"


# ---------------------------------------------------------------------------
# Settings container
# ---------------------------------------------------------------------------

@dataclass
class AISettings:
    api_key: str = ""
    selected_model: str = DEFAULT_MODEL
    image_model: str = DEFAULT_IMAGE_MODEL
    enabled: bool = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_text(value: Any, fallback: str = "") -> str:
    if not isinstance(value, str):
        return fallback
    return value.strip() or fallback


def get_user_config_dir() -> Path:
    # Keep settings beside the rest of the mutable application data. On
    # Railway this resolves to /data/edeka-promo-tool by default, so attaching
    # a volume at /data makes API settings and uploaded products persistent.
    return settings.data_dir


def get_settings_path() -> Path:
    return get_user_config_dir() / "settings.json"


# ---------------------------------------------------------------------------
# Persistence + migration (handles old multi-provider format)
# ---------------------------------------------------------------------------

def load_user_settings() -> AISettings:
    path = get_settings_path()
    if not path.exists():
        return AISettings()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("settings.json konnte nicht gelesen werden: %s", e)
        return AISettings()

    # Old multi-provider format → migrate to simple format
    if "providers" in data and isinstance(data["providers"], list):
        providers = data["providers"]
        # Find first enabled provider and extract key + model
        for p in providers:
            if isinstance(p, dict) and p.get("enabled", True) and p.get("api_key"):
                logger.info("Altes Mehr-Anbieter-Format migriert")
                return AISettings(
                    api_key=_clean_text(p.get("api_key")),
                    selected_model=_clean_text(p.get("model"), DEFAULT_MODEL),
                    image_model=DEFAULT_IMAGE_MODEL,
                )
        # No enabled provider with key → keep empty
        return AISettings()

    # Old single-provider format
    if "provider" in data:
        logger.info("Altes Einzel-Anbieter-Format migriert")
        return AISettings(
            api_key=_clean_text(data.get("api_key")),
            selected_model=_clean_text(data.get("model"), DEFAULT_MODEL),
            image_model=_clean_text(data.get("image_model"), DEFAULT_IMAGE_MODEL),
        )

    # New simple format
    return AISettings(
        api_key=_clean_text(data.get("api_key")),
        selected_model=_clean_text(data.get("selected_model"), DEFAULT_MODEL),
        image_model=_clean_text(data.get("image_model"), DEFAULT_IMAGE_MODEL),
        enabled=data.get("enabled", True),
    )


def save_user_settings(next_settings: AISettings) -> AISettings:
    path = get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "api_key": next_settings.api_key,
        "selected_model": next_settings.selected_model,
        "image_model": next_settings.image_model,
        "enabled": next_settings.enabled,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return next_settings


def get_effective_ai_settings() -> AISettings:
    """Merge user settings with env fallback."""
    user = load_user_settings()
    api_key = user.api_key or settings.openrouter_api_key
    model = user.selected_model or DEFAULT_MODEL
    image_model = user.image_model or settings.openrouter_image_model or DEFAULT_IMAGE_MODEL
    return AISettings(api_key=api_key, selected_model=model, image_model=image_model, enabled=user.enabled)


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 10:
        return "••••"
    return f"{api_key[:6]}••••{api_key[-4:]}"
