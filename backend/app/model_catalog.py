"""Hardcoded catalog of free/cheap OpenRouter models with vision support.

All models are available through OpenRouter with a single API key.
Prices are per million tokens. Cost per design is estimated for our
~500-token system prompt + ~300-token user prompt + ~800-token image
+ ~400-token JSON response = ~2000 tokens total.
"""

MODEL_CATALOG: list[dict] = [
    # ── Free models with vision ──────────────────────────────────────
    {
        "id": "google/gemma-4-31b-it:free",
        "name": "Gemma 4 31B",
        "provider": "Google",
        "vision": True,
        "free": True,
        "cost_per_million_input": 0,
        "cost_per_million_output": 0,
        "cost_est_design": "0,00 €",
        "quality": 65,
        "context": "262K",
        "description": "Bestes kostenloses Vision-Modell. Gut für Farbanalyse und Designplanung.",
    },
    {
        "id": "google/gemma-4-26b-a4b-it:free",
        "name": "Gemma 4 26B A4B",
        "provider": "Google",
        "vision": True,
        "free": True,
        "cost_per_million_input": 0,
        "cost_per_million_output": 0,
        "cost_est_design": "0,00 €",
        "quality": 52,
        "context": "262K",
        "description": "Kompakter, schneller. Bildanalyse und Text in einem.",
    },
    {
        "id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "name": "Nemotron Nano Omni 30B",
        "provider": "NVIDIA",
        "vision": True,
        "free": True,
        "cost_per_million_input": 0,
        "cost_per_million_output": 0,
        "cost_est_design": "0,00 €",
        "quality": 36,
        "context": "256K",
        "description": "Multimodales Modell. Sieht Bilder und antwortet strukturiert.",
    },
    {
        "id": "nvidia/nemotron-nano-12b-v2-vl:free",
        "name": "Nemotron Nano 12B Vision",
        "provider": "NVIDIA",
        "vision": True,
        "free": True,
        "cost_per_million_input": 0,
        "cost_per_million_output": 0,
        "cost_est_design": "0,00 €",
        "quality": 25,
        "context": "128K",
        "description": "Kleinstes freies Vision-Modell. Reicht für einfache Planung.",
    },
    {
        "id": "openrouter/free",
        "name": "Free Router (Auto)",
        "provider": "OpenRouter",
        "vision": True,
        "free": True,
        "cost_per_million_input": 0,
        "cost_per_million_output": 0,
        "cost_est_design": "0,00 €",
        "quality": 45,
        "context": "200K",
        "description": "Wählt automatisch das beste verfügbare kostenlose Modell.",
    },
    # ── Free models without vision (text-only) ─────────────────────────
    {
        "id": "nvidia/nemotron-3-super-120b-a12b:free",
        "name": "Nemotron 3 Super 120B",
        "provider": "NVIDIA",
        "vision": False,
        "free": True,
        "cost_per_million_input": 0,
        "cost_per_million_output": 0,
        "cost_est_design": "0,00 €",
        "quality": 60,
        "context": "1.0M",
        "description": "Stärkstes freies Textmodell. Keine Bildanalyse, aber präzise Planung.",
    },
    {
        "id": "openai/gpt-oss-120b:free",
        "name": "GPT-OSS 120B",
        "provider": "OpenAI",
        "vision": False,
        "free": True,
        "cost_per_million_input": 0,
        "cost_per_million_output": 0,
        "cost_est_design": "0,00 €",
        "quality": 55,
        "context": "131K",
        "description": "OpenAIs freies Modell. Gut für kreative Textvorschläge.",
    },
    # ── Ultra-cheap models (cents per design) ──────────────────────────
    {
        "id": "openai/gpt-4o-mini",
        "name": "GPT-4o Mini",
        "provider": "OpenAI",
        "vision": True,
        "free": False,
        "cost_per_million_input": 0.15,
        "cost_per_million_output": 0.60,
        "cost_est_design": "~0,0004 €",
        "quality": 70,
        "context": "128K",
        "description": "Günstigstes Vision-Modell mit Top-Qualität. < 0,1 Cent pro Design.",
    },
    {
        "id": "google/gemini-2.5-flash-lite",
        "name": "Gemini 2.5 Flash Lite",
        "provider": "Google",
        "vision": True,
        "free": False,
        "cost_per_million_input": 0.10,
        "cost_per_million_output": 0.40,
        "cost_est_design": "~0,0003 €",
        "quality": 68,
        "context": "1.0M",
        "description": "Sehr günstig mit großem Kontext. Ideal für Bild+Text.",
    },
    {
        "id": "meta-llama/llama-4-maverick",
        "name": "Llama 4 Maverick 17B",
        "provider": "Meta",
        "vision": True,
        "free": False,
        "cost_per_million_input": 0.15,
        "cost_per_million_output": 0.60,
        "cost_est_design": "~0,0004 €",
        "quality": 55,
        "context": "256K",
        "description": "Open-Source Vision-Modell. Gut und günstig.",
    },
    {
        "id": "qwen/qwen3.5-122b-a10b",
        "name": "Qwen 3.5 122B A10B",
        "provider": "Qwen",
        "vision": True,
        "free": False,
        "cost_per_million_input": 0.30,
        "cost_per_million_output": 0.70,
        "cost_est_design": "~0,0007 €",
        "quality": 70,
        "context": "262K",
        "description": "Starkes multimodales Modell. Gute Farb- und Layoutanalyse.",
    },
]

def get_model_catalog() -> list[dict]:
    return MODEL_CATALOG

def get_model_by_id(model_id: str) -> dict | None:
    for m in MODEL_CATALOG:
        if m["id"] == model_id:
            return m
    return None
