"""EDEKA Promo Tool launcher.

Starts the local API/UI server and opens it as a desktop window:
  1. a native OS window (pywebview: WebView2 on Windows, WKWebView on macOS,
     WebKitGTK on Linux),
  2. otherwise a chrome-less app window via an installed Chromium browser
     (--app mode; on Windows, Edge is always present),
  3. otherwise the default browser.
"""
import os
import sys
import time
import shutil
import threading
import subprocess
import tempfile
import webbrowser
import urllib.request
from pathlib import Path

import uvicorn
from app.main import app

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"
TITLE = "EDEKA Mühlenbein – Promo Studio"


def _run_server() -> None:
    uvicorn.run(app, host=HOST, port=PORT, reload=False, log_level="warning")


def _wait_ready(timeout: float = 40.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{URL}/health", timeout=1):
                return True
        except Exception:
            time.sleep(0.25)
    return False


def _open_native_window() -> bool:
    """Native window via pywebview. Blocks until the window is closed."""
    try:
        import webview  # noqa: WPS433
    except Exception:
        return False
    try:
        webview.create_window(TITLE, URL, width=1280, height=860, min_size=(1024, 720))
        webview.start()
        return True
    except Exception:
        return False


def _find_chromium() -> str | None:
    if sys.platform == "darwin":
        for path in (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ):
            if Path(path).exists():
                return path
        return None
    if sys.platform.startswith("win"):
        bases = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        for base in bases:
            if not base:
                continue
            for rel in (
                r"Microsoft\Edge\Application\msedge.exe",
                r"Google\Chrome\Application\chrome.exe",
                r"BraveSoftware\Brave-Browser\Application\brave.exe",
            ):
                p = Path(base) / rel
                if p.exists():
                    return str(p)
        return None
    for name in (
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
        "brave-browser", "microsoft-edge", "microsoft-edge-stable",
    ):
        found = shutil.which(name)
        if found:
            return found
    return None


def _open_app_window() -> bool:
    """Chrome-less app window via a Chromium browser. Blocks until closed."""
    browser = _find_chromium()
    if not browser:
        return False
    profile = Path(tempfile.gettempdir()) / "edeka-promo-app-profile"
    try:
        proc = subprocess.Popen([
            browser,
            f"--app={URL}",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-size=1280,860",
        ])
        proc.wait()
        return True
    except Exception:
        return False


def main() -> None:
    threading.Thread(target=_run_server, daemon=True).start()
    if not _wait_ready():
        print(f"Server konnte nicht gestartet werden. Bitte {URL} manuell öffnen.")
        sys.exit(1)

    if _open_native_window():
        return
    if _open_app_window():
        return

    webbrowser.open(URL)
    print(f"EDEKA Promo Tool läuft: {URL}  (zum Beenden dieses Fenster schließen)")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
