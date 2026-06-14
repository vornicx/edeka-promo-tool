import json
import logging
from openai import AsyncOpenAI
from app.adapters.base import AIAdapter
from app.config import settings

logger = logging.getLogger(__name__)


class OpenRouterAdapter(AIAdapter):
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        self.model = settings.openrouter_model

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
            raise ValueError("La API de IA devolvió una respuesta vacía")
        content = response.choices[0].message.content
        if not content:
            raise ValueError("La API de IA devolvió contenido vacío")
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
            logger.error("JSON inválido recibido de IA: %s", cleaned[:200])
            raise ValueError(f"La IA devolvió JSON inválido: {e}") from e

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
