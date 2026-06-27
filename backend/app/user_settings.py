import json
import logging
import os
import sys
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

APP_NAME = "EDEKA Promo Tool"


# ---------------------------------------------------------------------------
# Provider config
# ---------------------------------------------------------------------------

@dataclass
class ProviderConfig:
    id: str
    type: str                          # "openrouter" | "gemini" | "github" | "nvidia" | "ollama" | "custom"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderConfig":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            type=_clean_text(data.get("type"), "openrouter"),
            api_key=_clean_text(data.get("api_key")),
            base_url=_clean_text(data.get("base_url")),
            model=_clean_text(data.get("model")),
            enabled=data.get("enabled", True),
        )


# ---------------------------------------------------------------------------
# Settings container
# ---------------------------------------------------------------------------

@dataclass
class AISettings:
    providers: list[ProviderConfig] = field(default_factory=list)

    def get_enabled_providers(self) -> list[ProviderConfig]:
        return [p for p in self.providers if p.enabled]


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
# Persistence + migration
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

    # Detect old single-provider format → auto-migrate
    if "provider" in data and "providers" not in data:
        logger.info("Altes settings.json-Format erkannt, migriere zu neuem Format")
        provider = ProviderConfig(
            id="auto-migrated-1",
            type=_clean_text(data.get("provider"), "openrouter"),
            api_key=_clean_text(data.get("api_key")),
            base_url=_clean_text(data.get("base_url"), "https://openrouter.ai/api/v1"),
            model=_clean_text(data.get("model"), "openai/gpt-4o-mini"),
            enabled=True,
        )
        return AISettings(providers=[provider])

    providers = [
        ProviderConfig.from_dict(p)
        for p in data.get("providers", [])
        if isinstance(p, dict) and p.get("type")
    ]
    return AISettings(providers=providers)


def save_user_settings(next_settings: AISettings) -> AISettings:
    path = get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"providers": [p.to_dict() for p in next_settings.providers]}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return next_settings


# ---------------------------------------------------------------------------
# Effective settings (env-based defaults merged with user config)
# ---------------------------------------------------------------------------

_EFFECTIVE_PROVIDER_DEFAULTS: dict[str, dict] = {
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "model": "openai/gpt-4o-mini"},
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o"},
    "anthropic": {"base_url": "https://api.anthropic.com", "model": "claude-sonnet-4-20250514"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-2.5-flash"},
    "github": {"base_url": "https://models.inference.ai.azure.com", "model": "gpt-4o-mini"},
    "nvidia": {"base_url": "https://integrate.api.nvidia.com/v1", "model": "nvidia/nemotron-3-nano-omni-30b-a3b"},
    "ollama": {"base_url": "http://localhost:11434", "model": "gemma4:2b"},
    "custom": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
}


def get_effective_ai_settings() -> AISettings:
    """Merge user settings with environment defaults, returning the resolved list."""
    user = load_user_settings()
    if user.providers:
        for p in user.providers:
            defaults = _EFFECTIVE_PROVIDER_DEFAULTS.get(p.type, {})
            if not p.base_url:
                p.base_url = defaults.get("base_url", "")
            if not p.model:
                p.model = defaults.get("model", "")
        return user

    # No saved providers: seed with a default OpenRouter entry using env credentials (legacy)
    env_api_key = settings.openrouter_api_key or ""
    return AISettings(providers=[
        ProviderConfig(
            id="default",
            type="openrouter",
            api_key=env_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            enabled=True,
        )
    ])


# ---------------------------------------------------------------------------
# API key masking
# ---------------------------------------------------------------------------

def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 10:
        return "••••"
    return f"{api_key[:6]}••••{api_key[-4:]}"
