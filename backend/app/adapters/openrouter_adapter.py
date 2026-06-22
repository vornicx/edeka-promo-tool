import json
import logging
from openai import AsyncOpenAI
from app.adapters.base import AIAdapter
from app.user_settings import get_effective_ai_settings

logger = logging.getLogger(__name__)


class OpenRouterAdapter(AIAdapter):
    def __init__(self):
        ai_settings = get_effective_ai_settings()
        if not ai_settings.api_key:
            raise ValueError("Keine API-Key hinterlegt. Der lokale Profi-Modus erstellt die Promotion ohne KI-Kosten.")
        self.client = AsyncOpenAI(
            api_key=ai_settings.api_key,
            base_url=ai_settings.base_url,
        )
        self.model = ai_settings.model

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not response.choices:
            raise ValueError("Die KI-API hat eine leere Antwort geliefert")
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Die KI-API hat keinen Inhalt geliefert")
        return content

    def _parse_json_response(self, text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Ungueltiges JSON von KI erhalten: %s", cleaned[:200])
            raise ValueError(f"Die KI hat ungueltiges JSON geliefert: {e}") from e

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> dict:
        response_text = await self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self._parse_json_response(response_text)
