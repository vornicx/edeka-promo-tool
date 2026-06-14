from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes.promo import router as promo_router

app = FastAPI(
    title="EDEKA Mühlenbein Promo Tool",
    description="Herramienta de creación de promociones con IA",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(promo_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "model": settings.openrouter_model}
