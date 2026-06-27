from typing import Optional
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.user_settings import (
    AISettings,
    ProviderConfig,
    get_effective_ai_settings,
    get_settings_path,
    load_user_settings,
    mask_api_key,
    save_user_settings,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ProviderPublic(BaseModel):
    id: str
    type: str
    base_url: str
    model: str
    enabled: bool
    has_api_key: bool
    masked_api_key: str


class ProviderPayload(BaseModel):
    id: str
    type: str = "openrouter"
    api_key: Optional[str] = None
    base_url: str = ""
    model: str = ""
    enabled: bool = True


class SettingsResponse(BaseModel):
    providers: list[ProviderPublic]
    settings_path: str


class SaveSettingsRequest(BaseModel):
    providers: list[ProviderPayload]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def _to_public(p: ProviderConfig) -> ProviderPublic:
    return ProviderPublic(
        id=p.id,
        type=p.type,
        base_url=p.base_url,
        model=p.model,
        enabled=p.enabled,
        has_api_key=bool(p.api_key),
        masked_api_key=mask_api_key(p.api_key),
    )


@router.get("")
async def get_settings() -> SettingsResponse:
    effective = get_effective_ai_settings()
    return SettingsResponse(
        providers=[_to_public(p) for p in effective.providers],
        settings_path=str(get_settings_path()),
    )


@router.put("")
async def update_settings(request: SaveSettingsRequest) -> SettingsResponse:
    updated: list[ProviderConfig] = []

    for i, payload in enumerate(request.providers):
        provider_type = payload.type.strip() or "openrouter"
        base_url = payload.base_url.strip().rstrip("/")
        model = payload.model.strip()

        if not base_url:
            raise HTTPException(status_code=400, detail=f"Basis-URL für Anbieter {i+1} ist erforderlich")
        if not model:
            raise HTTPException(status_code=400, detail=f"Modell für Anbieter {i+1} ist erforderlich")

        # Preserve existing API key if not sent (partial update)
        previous = load_user_settings()
        existing = {p.id: p for p in previous.providers}.get(payload.id)
        api_key = payload.api_key
        if api_key is None and existing:
            api_key = existing.api_key
        elif isinstance(api_key, str):
            api_key = api_key.strip()

        updated.append(ProviderConfig(
            id=payload.id or uuid.uuid4().hex[:12],
            type=provider_type,
            api_key=api_key or "",
            base_url=base_url,
            model=model,
            enabled=payload.enabled,
        ))

    save_user_settings(AISettings(providers=updated))
    return SettingsResponse(
        providers=[_to_public(p) for p in updated],
        settings_path=str(get_settings_path()),
    )
