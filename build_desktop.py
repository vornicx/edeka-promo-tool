#!/usr/bin/env python3
"""
Build script for EDEKA Promo Tool desktop executable.
Run from project root: python build_desktop.py
"""

import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DIST_DIR = PROJECT_ROOT / "dist"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"


def build_frontend():
    print("=== Building frontend (Next.js static export) ===")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Frontend build failed:")
        print(result.stderr)
        sys.exit(1)
    print("Frontend build OK")
    out_dir = FRONTEND_DIR / "out"
    if not out_dir.exists():
        print("ERROR: frontend/out/ not found after build")
        sys.exit(1)
    return out_dir


def build_exe(frontend_out: Path):
    print("=== Building executable with PyInstaller ===")
    dist_dir = PROJECT_ROOT / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "edeka-promo-tool",
        "--add-data", f"{frontend_out}{':' if sys.platform != 'win32' else ';'}frontend/out",
        "--add-data", f"{BACKEND_DIR / 'app' / 'assets'}{':' if sys.platform != 'win32' else ';'}app/assets",
        "--hidden-import", "openai",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._imagingft",
        "--hidden-import", "pydantic",
        "--hidden-import", "pydantic_settings",
        "--hidden-import", "httpx",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.middleware",
        "--hidden-import", "fastapi",
        "--collect-all", "app",
        str(BACKEND_DIR / "run.py"),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print("PyInstaller failed:")
        print(result.stderr)
        sys.exit(1)
    print(result.stdout)
    print("Executable created in dist/edeka-promo-tool.exe")


def main():
    frontend_out = build_frontend()
    build_exe(frontend_out)
    print("=== DONE ===")


if __name__ == "__main__":
    main()
