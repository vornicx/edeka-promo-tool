import os, sys
from pydantic_settings import BaseSettings
from pathlib import Path


def _is_cloud() -> bool:
    return bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("VERCEL") == "1" or os.environ.get("RENDER"))


_APP_DIR = Path(__file__).resolve().parent


def _user_data_dir() -> Path:
    app_name = "EDEKA Promo Tool"
    if sys.platform.startswith("win"):
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        return Path(root or Path.home() / "AppData" / "Local") / app_name
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "edeka-promo-tool"


def _cloud_data_dir() -> Path:
    configured = os.environ.get("PROMO_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()

    # Railway volumes can be mounted at /data. Keeping all mutable app state
    # below this path makes settings and uploaded products survive deploys once
    # a volume is attached. Without a volume the app still works, but the
    # container filesystem remains ephemeral.
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        return Path("/data") / "edeka-promo-tool"

    # Vercel/Render serverless filesystems are ephemeral and only /tmp is
    # guaranteed writable. The web app remains functional there, while durable
    # state should live on Railway (or another persistent service).
    return Path("/tmp/data") / "edeka-promo-tool"


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_image_model: str = "google/gemini-3.1-flash-image"

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
    def data_dir(self) -> Path:
        p = _cloud_data_dir() if _is_cloud() else _user_data_dir()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def output_dir(self) -> Path:
        p = self.data_dir / "output"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def assets_dir(self) -> Path:
        return _APP_DIR / "assets"

    @property
    def backgrounds_dir(self) -> Path:
        if _is_cloud():
            p = self.data_dir / "backgrounds"
        else:
            p = self.assets_dir / "backgrounds"
        p.mkdir(parents=True, exist_ok=True)
        return p

    model_config = {
        "env_file": str(_APP_DIR.parent / "env.local"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
