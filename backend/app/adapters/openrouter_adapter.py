import logging
from app.adapters.openai_compatible import OpenAICompatibleAdapter
from app.user_settings import get_effective_ai_settings

logger = logging.getLogger(__name__)


class OpenRouterAdapter(OpenAICompatibleAdapter):
    """Legacy adapter — uses global settings. Internal use only for backward compat."""

    def __init__(self):
        ai_settings = get_effective_ai_settings()
        if not ai_settings.api_key:
            raise ValueError("Keine API-Key hinterlegt. Der lokale Profi-Modus erstellt die Promotion ohne KI-Kosten.")
        super().__init__(
            api_key=ai_settings.api_key,
            base_url=ai_settings.base_url,
            model=ai_settings.model,
        )
