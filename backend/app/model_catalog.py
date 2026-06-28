"""Catalog of cheap OpenRouter models for promo planning.

All models use one OpenRouter API key. Prices are per million tokens.
The studio asks the selected model for a compact JSON creative plan. Product
posters are rendered locally; AI event posters can additionally request one
generated photographic background via the configured image model.
Estimated cost assumes roughly 1.6K input tokens and 400 output tokens for
planning only.
"""

MODEL_CATALOG: list[dict] = [
    # Recommended low-cost models with vision.
    {
        "id": "google/gemini-2.5-flash-lite",
        "name": "Gemini 2.5 Flash Lite",
        "provider": "Google",
        "vision": True,
        "free": False,
        "cost_per_million_input": 0.10,
        "cost_per_million_output": 0.40,
        "cost_est_design": "~0,0003 EUR",
        "quality": 78,
        "context": "1M",
        "description": "Empfohlen: sehr gutes Preis-Leistungs-Verhaeltnis fuer Produktfoto-Analyse und kreative Designplanung.",
    },
    {
        "id": "openai/gpt-5-nano",
        "name": "GPT-5 Nano",
        "provider": "OpenAI",
        "vision": True,
        "free": False,
        "cost_per_million_input": 0.05,
        "cost_per_million_output": 0.40,
        "cost_est_design": "~0,0002 EUR",
        "quality": 72,
        "context": "400K",
        "description": "Sehr guenstig und schnell. Gute Wahl fuer viele Varianten ohne spuerbare Kosten.",
    },
    {
        "id": "bytedance-seed/seed-2.0-mini",
        "name": "Seed 2.0 Mini",
        "provider": "ByteDance",
        "vision": True,
        "free": False,
        "cost_per_million_input": 0.10,
        "cost_per_million_output": 0.40,
        "cost_est_design": "~0,0003 EUR",
        "quality": 68,
        "context": "256K",
        "description": "Kosten- und latenzoptimiertes Vision-Modell fuer einfache, schnelle Kampagnenplanung.",
    },
    {
        "id": "google/gemini-3.1-flash-lite-preview",
        "name": "Gemini 3.1 Flash Lite Preview",
        "provider": "Google",
        "vision": True,
        "free": False,
        "cost_per_million_input": 0.25,
        "cost_per_million_output": 1.50,
        "cost_est_design": "~0,0010 EUR",
        "quality": 84,
        "context": "1M",
        "description": "Mehr Qualitaet, immer noch extrem guenstig. Gut fuer anspruchsvollere Event- und Kampagnenideen.",
    },
    {
        "id": "qwen/qwen3.7-plus",
        "name": "Qwen 3.7 Plus",
        "provider": "Qwen",
        "vision": True,
        "free": False,
        "cost_per_million_input": 0.32,
        "cost_per_million_output": 1.28,
        "cost_est_design": "~0,0010 EUR",
        "quality": 80,
        "context": "1M",
        "description": "Starkes multimodales Modell mit gutem Verstaendnis fuer Layouts, Screens und visuelle Referenzen.",
    },
    {
        "id": "openai/gpt-5-mini",
        "name": "GPT-5 Mini",
        "provider": "OpenAI",
        "vision": True,
        "free": False,
        "cost_per_million_input": 0.25,
        "cost_per_million_output": 2.00,
        "cost_est_design": "~0,0012 EUR",
        "quality": 82,
        "context": "400K",
        "description": "Stabiler Allrounder fuer bessere Texte und solide kreative Richtungen, weiterhin weit unter 1 Cent.",
    },
    # Free options. Quality and availability can vary.
    {
        "id": "openrouter/free",
        "name": "Free Router (Auto)",
        "provider": "OpenRouter",
        "vision": True,
        "free": True,
        "cost_per_million_input": 0,
        "cost_per_million_output": 0,
        "cost_est_design": "0,00 EUR",
        "quality": 52,
        "context": "variabel",
        "description": "Gratis. OpenRouter waehlt ein verfuegbares freies Modell; Qualitaet und Tempo koennen schwanken.",
    },
    {
        "id": "google/gemma-4-31b-it:free",
        "name": "Gemma 4 31B (free)",
        "provider": "Google",
        "vision": True,
        "free": True,
        "cost_per_million_input": 0,
        "cost_per_million_output": 0,
        "cost_est_design": "0,00 EUR",
        "quality": 62,
        "context": "262K",
        "description": "Kostenloses Vision-Modell fuer einfache Fotoanalyse und Designideen.",
    },
    {
        "id": "nvidia/nemotron-3-super-120b-a12b:free",
        "name": "Nemotron 3 Super 120B (free)",
        "provider": "NVIDIA",
        "vision": False,
        "free": True,
        "cost_per_million_input": 0,
        "cost_per_million_output": 0,
        "cost_est_design": "0,00 EUR",
        "quality": 60,
        "context": "1M",
        "description": "Gratis und stark fuer Textplanung, aber ohne Produktfoto-Analyse.",
    },
]


def get_model_catalog() -> list[dict]:
    return MODEL_CATALOG


def get_model_by_id(model_id: str) -> dict | None:
    for m in MODEL_CATALOG:
        if m["id"] == model_id:
            return m
    return None
