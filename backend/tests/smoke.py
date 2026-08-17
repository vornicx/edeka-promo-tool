"""Small end-to-end smoke check for the production-critical Promo Studio flow."""

from __future__ import annotations

import os
import tempfile


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


with tempfile.TemporaryDirectory(prefix="edeka-promo-smoke-") as data_dir:
    # Configure mutable state before importing the FastAPI app/settings object.
    os.environ["PROMO_DATA_DIR"] = data_dir
    os.environ["PROMO_ALLOWED_ORIGINS"] = "https://edekamuhlenbein.vercel.app"

    from fastapi.testclient import TestClient

    from app.config import settings as app_settings
    from app.main import app

    # Set the secret explicitly so the smoke check does not depend on
    # environment-name parsing differences across runners.
    app_settings.openrouter_api_key = "smoke-secret-key-123456"

    client = TestClient(app)

    print("[1/6] health")
    health = client.get("/health")
    check(health.status_code == 200, f"health failed: {health.status_code} {health.text}")
    check(health.json()["status"] == "ok", f"unexpected health payload: {health.text}")

    print("[2/6] settings secrecy")
    settings_response = client.get("/api/settings")
    check(settings_response.status_code == 200, f"settings failed: {settings_response.status_code} {settings_response.text}")
    settings_body = settings_response.json()
    check(settings_body["has_api_key"] is True, f"API key was not detected: {settings_response.text}")
    check(settings_body["api_key"] == "", "stored API key was returned in api_key")
    check("smoke-secret-key" not in settings_response.text, "stored API key leaked in settings response")

    print("[3/6] create promotion")
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
    check(create.status_code == 200, f"create failed: {create.status_code} {create.text}")
    session_id = create.json()["session_id"]

    print("[4/6] compose variants")
    compose = client.post("/api/promo/compose_all", json={"session_id": session_id})
    check(compose.status_code == 200, f"compose failed: {compose.status_code} {compose.text}")
    variants = compose.json()["variants"]
    check(bool(variants), f"no variants returned: {compose.text}")

    print("[5/6] select and fetch image")
    select = client.post("/api/promo/select_variant", json={"session_id": session_id, "index": 0})
    check(select.status_code == 200, f"select failed: {select.status_code} {select.text}")

    image = client.get(f"/api/promo/image/{session_id}/variant/0")
    check(image.status_code == 200, f"image failed: {image.status_code} {image.text}")
    check(image.headers.get("content-type", "").startswith("image/png"), f"unexpected image type: {image.headers}")
    check(len(image.content) > 1_000, f"generated image is unexpectedly small: {len(image.content)} bytes")

    print("[6/6] export")
    export = client.post("/api/promo/export", json={"session_id": session_id, "format": "post"})
    check(export.status_code == 200, f"export failed: {export.status_code} {export.text}")
    check(len(export.content) > 1_000, f"export is unexpectedly small: {len(export.content)} bytes")

print("Promo Studio smoke test passed")
