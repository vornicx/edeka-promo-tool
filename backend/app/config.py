import os
from pydantic_settings import BaseSettings
from pathlib import Path


def _is_vercel() -> bool:
    return os.environ.get("VERCEL") == "1"


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:2b"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    base_dir: Path = Path(__file__).resolve().parent.parent

    @property
    def output_dir(self) -> Path:
        p = Path("/tmp/output") if _is_vercel() else self.base_dir / "output"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def assets_dir(self) -> Path:
        return self.base_dir / "assets"

    @property
    def backgrounds_dir(self) -> Path:
        p = Path("/tmp/backgrounds") if _is_vercel() else self.base_dir / "assets" / "backgrounds"
        p.mkdir(parents=True, exist_ok=True)
        return p

    model_config = {"env_file": "env.local", "env_file_encoding": "utf-8"}


settings = Settings()
