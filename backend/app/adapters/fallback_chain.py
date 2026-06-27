import logging
from app.adapters.base import AIAdapter

logger = logging.getLogger(__name__)


class FallbackChainExhausted(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        detail = "; ".join(errors)
        super().__init__(f"Alle KI-Anbieter waren nicht verfügbar: {detail}")


class FallbackChainAdapter(AIAdapter):
    supports_vision: bool = False

    def __init__(self, adapters: list[AIAdapter]):
        self._adapters = [a for a in adapters if a is not None]
        # Set vision support based on whether ANY adapter supports it
        self.supports_vision = any(a.supports_vision for a in self._adapters)

    async def _try_all(self, method: str, **kwargs) -> str:
        errors: list[str] = []
        for i, adapter in enumerate(self._adapters):
            try:
                func = getattr(adapter, method)
                return await func(**kwargs)
            except Exception as e:
                adapter_name = adapter.__class__.__name__
                err_msg = f"{adapter_name}: {e}"
                logger.warning("Fallback: %s failed — %s", adapter_name, e)
                errors.append(err_msg)
                if i == len(self._adapters) - 1:
                    raise FallbackChainExhausted(errors) from e
        raise FallbackChainExhausted(errors)

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        images: list[str] | None = None,
    ) -> str:
        return await self._try_all(
            "chat",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            images=images,
        )

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        images: list[str] | None = None,
    ) -> dict:
        return await self._try_all(
            "chat_json",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            images=images,
        )
