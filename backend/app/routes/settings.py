from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.user_settings import (
    AISettings,
    get_effective_ai_settings,
    get_settings_path,
    load_user_settings,
    mask_api_key,
    save_user_settings,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    provider: str
    base_url: str
    model: str
    has_api_key: bool
    masked_api_key: str
    settings_path: str


class SaveSettingsRequest(BaseModel):
    provider: str = "openrouter"
    api_key: Optional[str] = None
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "openai/gpt-4o-mini"


def _public_settings() -> SettingsResponse:
    current = get_effective_ai_settings()
    return SettingsResponse(
        provider=current.provider,
        base_url=current.base_url,
        model=current.model,
        has_api_key=bool(current.api_key),
        masked_api_key=mask_api_key(current.api_key),
        settings_path=str(get_settings_path()),
    )


@router.get("")
async def get_settings():
    return _public_settings()


@router.put("")
async def update_settings(request: SaveSettingsRequest):
    provider = request.provider.strip() or "openrouter"
    base_url = request.base_url.strip().rstrip("/")
    model = request.model.strip()

    if not base_url:
        raise HTTPException(status_code=400, detail="Die Basis-URL ist erforderlich")
    if not model:
        raise HTTPException(status_code=400, detail="Das Modell ist erforderlich")

    previous = load_user_settings()
    next_api_key = previous.api_key if request.api_key is None else request.api_key.strip()

    save_user_settings(
        AISettings(
            provider=provider,
            api_key=next_api_key,
            base_url=base_url,
            model=model,
        )
    )
    return _public_settings()
