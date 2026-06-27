import os, sys
from pydantic_settings import BaseSettings
from pathlib import Path


def _is_cloud() -> bool:
    return bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("VERCEL") == "1" or os.environ.get("RENDER"))


_APP_DIR = Path(__file__).resolve().parent


def _user_data_dir() -> Path:
    app_name = "EDEKA Promo Tool"
    if _is_cloud():
        return Path("/tmp/data") / "edeka-promo-tool"
    if sys.platform.startswith("win"):
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        return Path(root or Path.home() / "AppData" / "Local") / app_name
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "edeka-promo-tool"


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
        if _is_cloud():
            p = Path("/tmp/output")
        else:
            # Always use the per-user data directory (also in dev) so uploaded
            # products and settings live outside the repo and persist safely.
            p = _user_data_dir() / "output"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def assets_dir(self) -> Path:
        return _APP_DIR / "assets"

    @property
    def backgrounds_dir(self) -> Path:
        if _is_cloud():
            p = Path("/tmp/backgrounds")
        else:
            p = self.assets_dir / "backgrounds"
        p.mkdir(parents=True, exist_ok=True)
        return p

    model_config = {
        "env_file": str(_APP_DIR.parent / "env.local"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
