from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.user_settings import (
    AISettings,
    get_effective_ai_settings,
    get_settings_path,
    mask_api_key,
    save_user_settings,
)
from app.model_catalog import get_model_catalog, get_model_by_id

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SettingsResponse(BaseModel):
    api_key: str = ""
    selected_model: str = "openrouter/free"
    enabled: bool = True
    has_api_key: bool = False
    masked_api_key: str = ""
    settings_path: str = ""


class SaveSettingsRequest(BaseModel):
    api_key: Optional[str] = None
    selected_model: str = "openrouter/free"
    enabled: bool = True


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    vision: bool
    free: bool
    cost_est_design: str
    quality: int
    context: str
    description: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/models")
async def list_models() -> list[ModelInfo]:
    return [ModelInfo(**m) for m in get_model_catalog()]


@router.get("")
async def get_settings() -> SettingsResponse:
    effective = get_effective_ai_settings()
    return SettingsResponse(
        api_key=effective.api_key,
        selected_model=effective.selected_model,
        enabled=effective.enabled,
        has_api_key=bool(effective.api_key),
        masked_api_key=mask_api_key(effective.api_key),
        settings_path=str(get_settings_path()),
    )


@router.put("")
async def update_settings(request: SaveSettingsRequest) -> SettingsResponse:
    previous = get_effective_ai_settings()

    api_key = request.api_key
    if api_key is None:
        api_key = previous.api_key
    elif isinstance(api_key, str):
        api_key = api_key.strip()

    selected_model = request.selected_model.strip()
    if not selected_model:
        raise HTTPException(status_code=400, detail="Modell auswählen")

    # Validate model exists in catalog
    if not get_model_by_id(selected_model):
        # Allow any model ID, just warn
        pass

    next_settings = AISettings(api_key=api_key, selected_model=selected_model, enabled=request.enabled)
    save_user_settings(next_settings)

    return SettingsResponse(
        api_key=next_settings.api_key,
        selected_model=next_settings.selected_model,
        enabled=next_settings.enabled,
        has_api_key=bool(next_settings.api_key),
        masked_api_key=mask_api_key(next_settings.api_key),
        settings_path=str(get_settings_path()),
    )
