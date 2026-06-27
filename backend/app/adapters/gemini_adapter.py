import json
import logging
import httpx
from app.adapters.base import AIAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(AIAdapter):
    supports_vision = True

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        if not api_key:
            raise ValueError("Keine API-Key für Gemini hinterlegt")
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")

    def _build_parts(self, user_prompt: str, images: list[str] | None) -> list[dict]:
        parts: list[dict] = []
        if images:
            for img in images:
                # Gemini inlineData expects raw base64 (no data-URI prefix)
                if img.startswith("data:"):
                    # Format: data:image/png;base64,xxxx
                    header, b64 = img.split(",", 1)
                    mime_type = header.split(":")[1].split(";")[0]
                else:
                    mime_type = "image/png"
                    b64 = img
                parts.append({"inlineData": {"mimeType": mime_type, "data": b64}})
        parts.append({"text": user_prompt})
        return parts

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        images: list[str] | None = None,
    ) -> str:
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "user", "parts": [{"text": system_prompt}]})
            messages.append({"role": "model", "parts": [{"text": "Verstanden. Ich antworte im gewünschten Format."}]})
        messages.append({"role": "user", "parts": self._build_parts(user_prompt, images)})

        payload = {
            "contents": messages,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                response.raise_for_status()
                data = response.json()

            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Gemini hat keine Antwort geliefert")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise ValueError("Gemini hat leeren Inhalt geliefert")
            text = "".join(p.get("text", "") for p in parts)
            if not text:
                raise ValueError("Gemini hat keinen Text geliefert")
            return text
        except httpx.HTTPError as e:
            logger.error("Gemini-Verbindungsfehler: %s", e)
            raise ValueError(f"Gemini nicht erreichbar: {e}") from e

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
            logger.error("Ungültiges JSON von Gemini: %s", cleaned[:200])
            raise ValueError(f"Gemini hat ungültiges JSON geliefert: {e}") from e

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
