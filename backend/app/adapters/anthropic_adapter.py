import json
import logging
import httpx
from app.adapters.base import AIAdapter

logger = logging.getLogger(__name__)

ANTHROPIC_VERSION = "2023-06-01"


class AnthropicAdapter(AIAdapter):
    supports_vision = True

    DEFAULT_BASE_URL = "https://api.anthropic.com"

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        if not api_key:
            raise ValueError("Keine API-Key für Anthropic hinterlegt")
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")

    def _build_content(self, user_prompt: str, images: list[str] | None) -> list[dict]:
        content: list[dict] = []
        if images:
            for img in images:
                if img.startswith("data:image/png;base64,"):
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img.split(",", 1)[1],
                        },
                    })
                elif img.startswith("data:image/jpeg;base64,"):
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img.split(",", 1)[1],
                        },
                    })
                elif img.startswith("data:"):
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img.split(",", 1)[1],
                        },
                    })
                else:
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img,
                        },
                    })
        content.append({"type": "text", "text": user_prompt})
        return content

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        images: list[str] | None = None,
    ) -> str:
        payload: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": self._build_content(user_prompt, images)}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/messages",
                    json=payload,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": ANTHROPIC_VERSION,
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()

            content_blocks = data.get("content", [])
            if not content_blocks:
                raise ValueError("Claude hat keine Antwort geliefert")
            text = "".join(
                block.get("text", "") for block in content_blocks if block.get("type") == "text"
            )
            if not text:
                raise ValueError("Claude hat leeren Text geliefert")
            return text
        except httpx.HTTPError as e:
            logger.error("Claude-Verbindungsfehler: %s", e)
            raise ValueError(f"Claude nicht erreichbar: {e}") from e

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
            logger.error("Ungültiges JSON von Claude: %s", cleaned[:200])
            raise ValueError(f"Claude hat ungültiges JSON geliefert: {e}") from e

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
