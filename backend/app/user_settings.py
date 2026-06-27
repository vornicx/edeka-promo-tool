import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.config import settings


APP_NAME = "EDEKA Promo Tool"
DEFAULT_PROVIDER = "openrouter"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"


@dataclass
class AISettings:
    provider: str = DEFAULT_PROVIDER
    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL


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


def _clean_text(value: Any, fallback: str = "") -> str:
    if not isinstance(value, str):
        return fallback
    return value.strip() or fallback


def load_user_settings() -> AISettings:
    path = get_settings_path()
    if not path.exists():
        return AISettings()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AISettings()

    return AISettings(
        provider=_clean_text(data.get("provider"), DEFAULT_PROVIDER),
        api_key=_clean_text(data.get("api_key")),
        base_url=_clean_text(data.get("base_url"), DEFAULT_BASE_URL).rstrip("/"),
        model=_clean_text(data.get("model"), DEFAULT_MODEL),
    )


def save_user_settings(next_settings: AISettings) -> AISettings:
    path = get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(next_settings), indent=2), encoding="utf-8")
    return next_settings


def get_effective_ai_settings() -> AISettings:
    user = load_user_settings()
    api_key = user.api_key or settings.openrouter_api_key
    base_url = user.base_url or settings.openrouter_base_url
    model = user.model or settings.openrouter_model
    provider = user.provider or DEFAULT_PROVIDER
    return AISettings(provider=provider, api_key=api_key, base_url=base_url.rstrip("/"), model=model)


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 10:
        return "••••"
    return f"{api_key[:6]}••••{api_key[-4:]}"
