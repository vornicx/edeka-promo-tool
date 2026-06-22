#!/usr/bin/env python3
"""
Build EDEKA Promo Tool desktop executable (.exe).
Run: python build_desktop.py

Requires Docker installed.
"""

import shlex
import subprocess, sys, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
DIST = ROOT / "dist"
CLIENT_README = """EDEKA Muehlenbein Promo Tool fuer Windows

Nutzung:
1. edeka-promo-tool.exe starten.
2. Die App oeffnet sich im Browser.
3. KI-Einstellungen oeffnen.
4. API-Key eintragen, Anbieter/Modell waehlen und speichern.
5. Aktionen erstellen und exportieren.

Hinweise:
- Ohne API-Key nutzt die App den lokalen Profi-Modus.
- Der API-Key wird nur auf diesem Geraet gespeichert.
- Unter Windows liegt er in %APPDATA%\\EDEKA Promo Tool\\settings.json.
- Zum Beenden die Konsolenfenster des Programms schliessen.
"""


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


def ensure_docker_access():
    result = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("FAILED: Docker ist fuer diesen Benutzer nicht erreichbar.")
        print(result.stderr.strip())
        print("")
        print("Empfohlene Loesung:")
        print("  sudo usermod -aG docker $USER")
        print("  # Cierra sesión y vuelve a entrar")
        print("  python3 build_desktop.py")
        sys.exit(1)


def build_exe():
    print("=== Building Windows .exe (Docker PyInstaller) ===")
    ensure_docker_access()

    if DIST.exists():
        shutil.rmtree(DIST)

    data = [
        "frontend/out:frontend/out",
        "backend/app/assets:app/assets",
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

    pyinstaller_args = [
        "pyinstaller", "--onefile", "--name", "edeka-promo-tool",
        "-p", "backend",
    ]
    for d in data:
        pyinstaller_args += ["--add-data", d]
    for h in hidden:
        pyinstaller_args += ["--hidden-import", h]
    pyinstaller_args += ["--collect-all", "app", "backend/run.py"]

    build_command = (
        "pip install -r backend/requirements.txt && "
        + shlex.join(pyinstaller_args)
        + " && chown -R --reference=. dist"
    )

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{ROOT}:/src",
        "-w", "/src",
        "batonogov/pyinstaller-windows:python-3.12.2",
        build_command,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FAILED:", result.stderr)
        sys.exit(1)
    print(result.stdout)
    exe = DIST / "edeka-promo-tool.exe"
    if exe.exists():
        print(f"SUCCESS: {exe}")
        package_client_files(exe)
    else:
        print("WARNING: .exe not found")


def package_client_files(exe: Path):
    readme = DIST / "README_KUNDE.txt"
    readme.write_text(CLIENT_README, encoding="utf-8")
    package_dir = DIST / "edeka-promo-tool-windows"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)
    shutil.copy2(exe, package_dir / exe.name)
    shutil.copy2(readme, package_dir / readme.name)
    archive_base = DIST / "edeka-promo-tool-windows"
    archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=str(package_dir))
    print(f"PACKAGE: {archive_path}")


def main():
    build_frontend()
    build_exe()
    print("=== DONE ===")


if __name__ == "__main__":
    main()
