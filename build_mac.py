#!/usr/bin/env python3
"""
Build EDEKA Promo Tool for macOS.  MUST be run ON a Mac (PyInstaller can't
cross-compile to .app from Linux/Windows).

Requires: macOS, Python 3.10+, Node.js/npm.
Run:  python3 build_mac.py

Output:
- dist/mac/EDEKA Promo Tool.app
- dist/edeka-promo-tool-mac.zip
"""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
DIST = ROOT / "dist"
MAC_DIST = DIST / "mac"
VENV = ROOT / ".venv-build-mac"
APP_NAME = "EDEKA Promo Tool"

CLIENT_README = """EDEKA Promo Tool fuer macOS

Installation:
1. "EDEKA Promo Tool.app" in den Ordner "Programme" ziehen.
2. Beim ersten Start: Rechtsklick auf die App -> "Oeffnen" -> "Oeffnen".
3. Die App oeffnet sich im Browser unter http://localhost:8000

Nutzung:
- KI-Einstellungen oeffnen und (optional) API-Key eintragen.
- Ohne Key laeuft die App im lokalen Profi-Modus.
- Aktionen erstellen und im gewuenschten Format exportieren.

Der API-Key wird nur lokal gespeichert:
~/Library/Application Support/EDEKA Promo Tool/settings.json
"""

HIDDEN = [
    "openai", "PIL", "PIL._imagingft", "pydantic", "pydantic_settings", "httpx",
    "uvicorn", "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto",
    "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
    "uvicorn.middleware", "fastapi",
]


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    print("===", " ".join(cmd), "===")
    result = subprocess.run(cmd, cwd=str(cwd), text=True)
    if result.returncode != 0:
        sys.exit(result.returncode)


def build_icns() -> Path | None:
    """Generate an .icns app icon from the Waschbär PNG (macOS tools only)."""
    png = BACKEND / "app" / "assets" / "waschbaer_logo.png"
    if not png.exists() or not shutil.which("iconutil") or not shutil.which("sips"):
        return None
    iconset = DIST / "icon.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir(parents=True)
    for size in (16, 32, 64, 128, 256, 512):
        run(["sips", "-z", str(size), str(size), str(png),
             "--out", str(iconset / f"icon_{size}x{size}.png")])
        run(["sips", "-z", str(size * 2), str(size * 2), str(png),
             "--out", str(iconset / f"icon_{size}x{size}@2x.png")])
    icns = DIST / "icon.icns"
    run(["iconutil", "-c", "icns", str(iconset), "-o", str(icns)])
    return icns if icns.exists() else None


def main() -> None:
    if sys.platform != "darwin":
        sys.exit("Dieser Build muss auf einem Mac (macOS) ausgefuehrt werden.")

    run(["npm", "install"], cwd=FRONTEND)
    run(["npm", "run", "build"], cwd=FRONTEND)
    icns = build_icns()

    if not VENV.exists():
        run([sys.executable, "-m", "venv", str(VENV)])
    pip = VENV / "bin" / "pip"
    run([str(pip), "install", "-r", str(BACKEND / "requirements.txt"), "pyinstaller==6.11.1"])
    pyinstaller = VENV / "bin" / "pyinstaller"

    if MAC_DIST.exists():
        shutil.rmtree(MAC_DIST)

    cmd = [
        str(pyinstaller), "--noconfirm", "--clean", "--windowed", "--onedir",
        "--name", APP_NAME,
    ]
    if icns:
        cmd += ["--icon", str(icns)]
    cmd += [
        "--distpath", str(MAC_DIST),
        "--workpath", str(DIST / "mac-build"),
        "--specpath", str(DIST),
        "-p", str(BACKEND),
        "--add-data", f"{FRONTEND / 'out'}:frontend/out",
        "--add-data", f"{BACKEND / 'app' / 'assets'}:app/assets",
    ]
    for h in HIDDEN:
        cmd += ["--hidden-import", h]
    cmd += ["--collect-all", "app", str(BACKEND / "run.py")]
    run(cmd)

    app_path = MAC_DIST / f"{APP_NAME}.app"
    if not app_path.exists():
        sys.exit(f"Build fehlgeschlagen: {app_path} nicht gefunden")

    (MAC_DIST / "LIESMICH_MAC.txt").write_text(CLIENT_README, encoding="utf-8")

    zip_path = DIST / "edeka-promo-tool-mac.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in app_path.rglob("*"):
            zf.write(p, p.relative_to(MAC_DIST))
        zf.write(MAC_DIST / "LIESMICH_MAC.txt", "LIESMICH_MAC.txt")

    print(f"SUCCESS: {app_path}")
    print(f"PACKAGE: {zip_path}")


if __name__ == "__main__":
    main()
