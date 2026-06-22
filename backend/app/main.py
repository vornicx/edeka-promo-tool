import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes.promo import router as promo_router
from app.routes.settings import router as settings_router
from app.routes.products import router as products_router
from app.routes.examples import router as examples_router

app = FastAPI(
    title="EDEKA Mühlenbein Promo Tool",
    description="Tool zur Erstellung professioneller EDEKA-Aktionsmotive",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(promo_router)
app.include_router(settings_router)
app.include_router(products_router)
app.include_router(examples_router)


@app.get("/health")
async def health_check():
    from app.user_settings import get_effective_ai_settings

    ai_settings = get_effective_ai_settings()
    return {
        "status": "ok",
        "model": ai_settings.model,
        "provider": ai_settings.provider,
        "has_api_key": bool(ai_settings.api_key),
    }


if getattr(sys, "frozen", False):
    base_dir = Path(sys._MEIPASS)
else:
    base_dir = Path(__file__).resolve().parent.parent.parent
frontend_static = base_dir / "frontend" / "out"
if frontend_static.exists():
    app.mount("/", StaticFiles(directory=str(frontend_static), html=True), name="frontend")
