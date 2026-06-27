import json
import logging
import httpx
from app.adapters.base import AIAdapter

logger = logging.getLogger(__name__)


class OllamaAdapter(AIAdapter):
    supports_vision = True

    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        images: list[str] | None = None,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if images:
            # Ollama accepts base64 images directly (without data-URI prefix)
            processed = [img.split(",", 1)[1] if img.startswith("data:") else img for img in images]
            messages[-1]["images"] = processed

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": temperature, "num_predict": max_tokens},
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("message", {}).get("content", "")
                if not content:
                    raise ValueError("Ollama hat leeren Inhalt geliefert")
                return content
        except httpx.HTTPError as e:
            logger.error("Ollama-Verbindungsfehler: %s", e)
            raise ValueError(f"Ollama nicht erreichbar: {e}") from e

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
            logger.error("Ungültiges JSON von Ollama: %s", cleaned[:200])
            raise ValueError(f"Ollama hat ungültiges JSON geliefert: {e}") from e

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
