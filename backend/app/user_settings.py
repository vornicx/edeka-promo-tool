import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

APP_NAME = "EDEKA Promo Tool"

FREE_FALLBACK_MODELS = [
    "openrouter/free",                        # auto-selects best free model
    "google/gemma-4-31b-it:free",            # best free vision
    "nvidia/nemotron-3-super-120b-a12b:free", # best free text
]

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-2.5-flash-lite"


# ---------------------------------------------------------------------------
# Settings container
# ---------------------------------------------------------------------------

@dataclass
class AISettings:
    api_key: str = ""
    selected_model: str = DEFAULT_MODEL
    enabled: bool = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_text(value: Any, fallback: str = "") -> str:
    if not isinstance(value, str):
        return fallback
    return value.strip() or fallback


def get_user_config_dir() -> Path:
    if bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RENDER")):
        p = Path("/tmp/data") / "edeka-promo-tool"
        p.mkdir(parents=True, exist_ok=True)
        return p
    if sys.platform.startswith("win"):
        root = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(root) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "edeka-promo-tool"


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
                )
        # No enabled provider with key → keep empty
        return AISettings()

    # Old single-provider format
    if "provider" in data:
        logger.info("Altes Einzel-Anbieter-Format migriert")
        return AISettings(
            api_key=_clean_text(data.get("api_key")),
            selected_model=_clean_text(data.get("model"), DEFAULT_MODEL),
        )

    # New simple format
    return AISettings(
        api_key=_clean_text(data.get("api_key")),
        selected_model=_clean_text(data.get("selected_model"), DEFAULT_MODEL),
        enabled=data.get("enabled", True),
    )


def save_user_settings(next_settings: AISettings) -> AISettings:
    path = get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "api_key": next_settings.api_key,
        "selected_model": next_settings.selected_model,
        "enabled": next_settings.enabled,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return next_settings


def get_effective_ai_settings() -> AISettings:
    """Merge user settings with env fallback."""
    user = load_user_settings()
    api_key = user.api_key or settings.openrouter_api_key
    model = user.selected_model or DEFAULT_MODEL
    return AISettings(api_key=api_key, selected_model=model, enabled=user.enabled)


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 10:
        return "••••"
    return f"{api_key[:6]}••••{api_key[-4:]}"
