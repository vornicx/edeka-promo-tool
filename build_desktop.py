#!/usr/bin/env python3
"""
Build EDEKA Promo Tool desktop executable (.exe).
Run: python build_desktop.py

Requires Docker installed.
"""

import subprocess, sys, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
DIST = ROOT / "dist"


def build_frontend():
    print("=== Building frontend (Next.js static export) ===")
    result = subprocess.run(
        ["npm", "run", "build"], cwd=str(FRONTEND), capture_output=True, text=True
    )
    if result.returncode != 0:
        print("FAILED:", result.stderr)
        sys.exit(1)
    print("OK")
    return FRONTEND / "out"


def build_exe():
    print("=== Building Windows .exe (Docker PyInstaller) ===")
    if DIST.exists():
        shutil.rmtree(DIST)

    data = [
        f"{ROOT / 'frontend' / 'out'}{';'}frontend{';'}out",
        f"{BACKEND / 'app' / 'assets'}{';'}app{';'}assets",
    ]

    hidden = [
        "openai", "PIL", "PIL._imagingft",
        "pydantic", "pydantic_settings",
        "httpx", "uvicorn", "uvicorn.logging",
        "uvicorn.loops", "uvicorn.loops.auto",
        "uvicorn.protocols", "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.middleware",
        "fastapi",
    ]

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{ROOT}:/src",
        "-w", "/src",
        "marcelotduarte/pyinstaller-windows:python3.12",
        "pyinstaller", "--onefile", "--name", "edeka-promo-tool",
    ]
    for d in data:
        cmd += ["--add-data", d]
    for h in hidden:
        cmd += ["--hidden-import", h]
    cmd += ["--collect-all", "app", "backend/run.py"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FAILED:", result.stderr)
        sys.exit(1)
    print(result.stdout)
    exe = DIST / "edeka-promo-tool.exe"
    if exe.exists():
        print(f"SUCCESS: {exe}")
    else:
        print("WARNING: .exe not found")


def main():
    build_frontend()
    build_exe()
    print("=== DONE ===")


if __name__ == "__main__":
    main()
