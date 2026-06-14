from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:2b"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    base_dir: Path = Path(__file__).resolve().parent.parent
    output_dir: Path = base_dir / "output"
    assets_dir: Path = base_dir / "assets"
    backgrounds_dir: Path = assets_dir / "backgrounds"

    model_config = {"env_file": "env.local", "env_file_encoding": "utf-8"}


settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
settings.backgrounds_dir.mkdir(parents=True, exist_ok=True)
