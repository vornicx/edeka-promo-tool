import os, sys
from pydantic_settings import BaseSettings
from pathlib import Path


def _is_vercel() -> bool:
    return os.environ.get("VERCEL") == "1"


_APP_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:2b"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    @property
    def base_dir(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS)
        return _APP_DIR.parent

    @property
    def output_dir(self) -> Path:
        if _is_vercel():
            p = Path("/tmp/output")
        elif getattr(sys, "frozen", False):
            p = self.base_dir / "output"
        else:
            p = self.base_dir / "output"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def assets_dir(self) -> Path:
        return _APP_DIR / "assets"

    @property
    def backgrounds_dir(self) -> Path:
        if _is_vercel():
            p = Path("/tmp/backgrounds")
        else:
            p = self.assets_dir / "backgrounds"
        p.mkdir(parents=True, exist_ok=True)
        return p

    model_config = {"env_file": "env.local", "env_file_encoding": "utf-8"}


settings = Settings()
