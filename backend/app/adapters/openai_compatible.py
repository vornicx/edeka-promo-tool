import json
import logging
from openai import AsyncOpenAI
from app.adapters.base import AIAdapter

logger = logging.getLogger(__name__)


class OpenAICompatibleAdapter(AIAdapter):
    supports_vision = True

    def __init__(self, api_key: str, base_url: str, model: str):
        if not api_key:
            raise ValueError("Keine API-Key für diesen Anbieter hinterlegt")
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def _build_messages(self, system_prompt: str, user_prompt: str, images: list[str] | None):
        user_content: list[dict] = []
        if images:
            for img in images:
                # Accept both bare base64 and data-URI
                if img.startswith("data:"):
                    user_content.append({"type": "image_url", "image_url": {"url": img}})
                else:
                    user_content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}})
        user_content.append({"type": "text", "text": user_prompt})

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content if len(user_content) > 1 else user_prompt},
        ]

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        images: list[str] | None = None,
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self._build_messages(system_prompt, user_prompt, images),
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.error("OpenAI-kompatibler API-Fehler (%s): %s", self.model, e)
            raise ValueError(f"KI-Anbieter nicht erreichbar: {e}") from e

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
            logger.error("Ungültiges JSON von KI erhalten: %s", cleaned[:200])
            raise ValueError(f"Die KI hat ungültiges JSON geliefert: {e}") from e

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        images: list[str] | None = None,
    ) -> dict:
        response_text = await self.chat(system_prompt, user_prompt, temperature, max_tokens, images)
        return self._parse_json_response(response_text)
