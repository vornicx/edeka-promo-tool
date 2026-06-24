#!/usr/bin/env python3
"""
Build EDEKA Promo Tool for Windows.  Run ON Windows (e.g. GitHub Actions
windows-latest).  To build a Windows .exe FROM Linux, use build_desktop.py
(Docker/Wine) instead.

Requires: Windows, Python 3.10+, Node.js/npm.
Run:  python build_windows.py

Output:
- dist\\edeka-promo-tool.exe
- dist\\edeka-promo-tool-windows.zip
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
VENV_PY = sys.executable

CLIENT_README = """EDEKA Promo Tool fuer Windows

Nutzung:
1. edeka-promo-tool.exe starten.
2. Falls Windows warnt: "Weitere Informationen" -> "Trotzdem ausfuehren".
3. Die App oeffnet sich im Browser unter http://localhost:8000
4. KI-Einstellungen oeffnen, optional API-Key eintragen (ohne Key: lokaler Modus).
5. Aktionen erstellen und exportieren.

Der API-Key wird nur lokal gespeichert:
%LOCALAPPDATA%\\EDEKA Promo Tool\\settings.json
"""

HIDDEN = [
    "openai", "PIL", "PIL._imagingft", "pydantic", "pydantic_settings", "httpx",
    "uvicorn", "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto",
    "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
    "uvicorn.middleware", "fastapi",
]


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    print("===", " ".join(cmd), "===", flush=True)
    if subprocess.run(cmd, cwd=str(cwd)).returncode != 0:
        sys.exit(1)


def main() -> None:
    run(["npm", "install"], cwd=FRONTEND)
    run(["npm", "run", "build"], cwd=FRONTEND)
    run([VENV_PY, "-m", "pip", "install", "-r", str(BACKEND / "requirements.txt"), "pyinstaller==6.11.1"])

    # On Windows the --add-data separator is ';'
    sep = ";"
    cmd = [
        VENV_PY, "-m", "PyInstaller", "--onefile", "--clean", "--noconfirm",
        "--name", "edeka-promo-tool",
        "--distpath", str(DIST),
        "--workpath", str(DIST / "win-build"),
        "--specpath", str(DIST),
        "-p", str(BACKEND),
        "--add-data", f"{FRONTEND / 'out'}{sep}frontend/out",
        "--add-data", f"{BACKEND / 'app' / 'assets'}{sep}app/assets",
    ]
    for h in HIDDEN:
        cmd += ["--hidden-import", h]
    cmd += ["--collect-all", "app", str(BACKEND / "run.py")]
    run(cmd)

    exe = DIST / "edeka-promo-tool.exe"
    if not exe.exists():
        sys.exit("Build fehlgeschlagen: .exe nicht gefunden")

    pkg = DIST / "edeka-promo-tool-windows"
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    shutil.copy2(exe, pkg / exe.name)
    (pkg / "README_KUNDE.txt").write_text(CLIENT_README, encoding="utf-8")

    zip_path = DIST / "edeka-promo-tool-windows.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(exe, exe.name)
        zf.write(pkg / "README_KUNDE.txt", "README_KUNDE.txt")

    print(f"SUCCESS: {exe}")
    print(f"PACKAGE: {zip_path}")


if __name__ == "__main__":
    main()
