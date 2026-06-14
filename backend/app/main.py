import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes.promo import router as promo_router

app = FastAPI(
    title="EDEKA Mühlenbein Promo Tool",
    description="Herramienta de creación de promociones con IA",
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


@app.get("/health")
async def health_check():
    return {"status": "ok", "model": settings.openrouter_model}


if getattr(sys, "frozen", False):
    base_dir = Path(sys._MEIPASS)
else:
    base_dir = Path(__file__).resolve().parent.parent.parent
frontend_static = base_dir / "frontend" / "out"
if frontend_static.exists():
    app.mount("/", StaticFiles(directory=str(frontend_static), html=True), name="frontend")
