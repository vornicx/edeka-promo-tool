"""Small end-to-end smoke check for the production-critical Promo Studio flow."""

from __future__ import annotations

import os
import tempfile


with tempfile.TemporaryDirectory(prefix="edeka-promo-smoke-") as data_dir:
    # Configure mutable state before importing the FastAPI app/settings object.
    os.environ["PROMO_DATA_DIR"] = data_dir
    os.environ["OPENROUTER_API_KEY"] = "smoke-secret-key-123456"
    os.environ["PROMO_ALLOWED_ORIGINS"] = "https://edekamuhlenbein.vercel.app"

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200, health.text
    assert health.json()["status"] == "ok"

    # A stored/environment API key must never be returned to the browser.
    settings = client.get("/api/settings")
    assert settings.status_code == 200, settings.text
    settings_body = settings.json()
    assert settings_body["has_api_key"] is True
    assert settings_body["api_key"] == ""
    assert "smoke-secret-key" not in settings.text

    create = client.post(
        "/api/promo/create",
        json={
            "campaign_kind": "product",
            "product": "Erdbeeren aus der Region",
            "category": "obst",
            "price": "2,99 €",
            "old_price": "3,99 €",
            "validity": "Nur diese Woche",
            "origin": "Deutschland",
            "claim": "Süß und frisch",
            "format": "post",
            "style": "edeka",
            "tone": "fresco",
            "price_size": "auto",
            "items": [],
            "use_ai_planning": False,
        },
    )
    assert create.status_code == 200, create.text
    session_id = create.json()["session_id"]

    compose = client.post("/api/promo/compose_all", json={"session_id": session_id})
    assert compose.status_code == 200, compose.text
    variants = compose.json()["variants"]
    assert variants, compose.text

    select = client.post("/api/promo/select_variant", json={"session_id": session_id, "index": 0})
    assert select.status_code == 200, select.text

    image = client.get(f"/api/promo/image/{session_id}/variant/0")
    assert image.status_code == 200, image.text
    assert image.headers.get("content-type", "").startswith("image/png")
    assert len(image.content) > 10_000

    export = client.post("/api/promo/export", json={"session_id": session_id, "format": "post"})
    assert export.status_code == 200, export.text
    assert len(export.content) > 10_000

print("Promo Studio smoke test passed")
