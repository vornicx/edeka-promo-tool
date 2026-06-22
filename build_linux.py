#!/usr/bin/env python3
"""
Build EDEKA Promo Tool for Linux.

Output:
- dist/linux/edeka-promo-tool
- dist/edeka-promo-tool-linux.tar.gz
"""

import shlex
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
DIST = ROOT / "dist"
LINUX_DIST = DIST / "linux"
PACKAGE_DIR = DIST / "edeka-promo-tool-linux"
VENV = ROOT / ".venv-build-linux"

APP_NAME = "edeka-promo-tool"
DISPLAY_NAME = "EDEKA Promo Tool"

CLIENT_README = """EDEKA Promo Tool fuer Linux

Installation:
1. Dieses Paket entpacken.
2. ./install.sh ausfuehren.
3. "EDEKA Promo Tool" im Anwendungsmenue oeffnen.

Nutzung:
1. KI-Einstellungen oeffnen.
2. API-Key eintragen. Ohne Key nutzt die App den lokalen Profi-Modus.
3. Anbieter und Modell speichern.
4. Aktionen erstellen und exportieren.

Der API-Key wird nur lokal gespeichert:
~/.config/edeka-promo-tool/settings.json
"""

INSTALL_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/edeka-promo-tool"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
LOG_FILE="$APP_DIR/edeka-promo-tool.log"

mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR"
cp "$SCRIPT_DIR/edeka-promo-tool" "$APP_DIR/edeka-promo-tool-server"
chmod +x "$APP_DIR/edeka-promo-tool-server"

cat > "$APP_DIR/edeka-promo-tool" <<'LAUNCHER'
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$HOME/.local/share/edeka-promo-tool"
LOG_FILE="$APP_DIR/edeka-promo-tool.log"
URL="http://127.0.0.1:8000"

if curl -fsS "$URL/health" >/dev/null 2>&1; then
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 &
  else
    echo "$URL"
  fi
  exit 0
fi

"$APP_DIR/edeka-promo-tool-server" > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" >/dev/null 2>&1 || true' INT TERM

for _ in $(seq 1 40); do
  if curl -fsS "$URL/health" >/dev/null 2>&1; then
    if command -v xdg-open >/dev/null 2>&1; then
      xdg-open "$URL" >/dev/null 2>&1 &
    else
      echo "$URL"
    fi
    wait "$SERVER_PID"
    exit $?
  fi
  sleep 0.25
done

kill "$SERVER_PID" >/dev/null 2>&1 || true
echo "EDEKA Promo Tool konnte nicht gestartet werden. Logdatei: $LOG_FILE" >&2
exit 1
LAUNCHER

chmod +x "$APP_DIR/edeka-promo-tool"
ln -sf "$APP_DIR/edeka-promo-tool" "$BIN_DIR/edeka-promo-tool"

cat > "$DESKTOP_DIR/edeka-promo-tool.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=EDEKA Promo Tool
Comment=Promotionen mit KI und lokalem Profi-Modus erstellen
Exec=edeka-promo-tool
Terminal=false
Categories=Office;Graphics;
DESKTOP

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

echo "Installiert: EDEKA Promo Tool"
echo "Startdatei: $BIN_DIR/edeka-promo-tool"
"""


def run(cmd: list[str], cwd: Path = ROOT):
    printable = shlex.join(cmd)
    print(f"=== {printable} ===")
    result = subprocess.run(cmd, cwd=str(cwd), text=True)
    if result.returncode != 0:
        sys.exit(result.returncode)


def build_frontend():
    print("=== Building frontend (Next.js static export) ===")
    run(["npm", "run", "build"], cwd=FRONTEND)


def ensure_venv():
    if not VENV.exists():
        run([sys.executable, "-m", "venv", str(VENV)])
    pip = VENV / "bin" / "pip"
    run([str(pip), "install", "-r", str(BACKEND / "requirements.txt"), "pyinstaller==6.11.1"])
    return VENV / "bin" / "pyinstaller"


def build_binary(pyinstaller: Path):
    print("=== Building Linux executable (PyInstaller) ===")
    if LINUX_DIST.exists():
        shutil.rmtree(LINUX_DIST)

    hidden = [
        "openai",
        "PIL",
        "PIL._imagingft",
        "pydantic",
        "pydantic_settings",
        "httpx",
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.middleware",
        "fastapi",
    ]

    cmd = [
        str(pyinstaller),
        "--onefile",
        "--clean",
        "--name",
        APP_NAME,
        "--distpath",
        str(LINUX_DIST),
        "--workpath",
        str(DIST / "linux-build"),
        "--specpath",
        str(DIST),
        "-p",
        str(BACKEND),
        "--add-data",
        f"{FRONTEND / 'out'}:frontend/out",
        "--add-data",
        f"{BACKEND / 'app' / 'assets'}:app/assets",
    ]
    for item in hidden:
        cmd += ["--hidden-import", item]
    cmd += ["--collect-all", "app", str(BACKEND / "run.py")]
    run(cmd)


def package_linux():
    print("=== Packaging Linux installer ===")
    binary = LINUX_DIST / APP_NAME
    if not binary.exists():
        raise FileNotFoundError(binary)

    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True)

    shutil.copy2(binary, PACKAGE_DIR / APP_NAME)
    (PACKAGE_DIR / "LEEME_LINUX.txt").write_text(CLIENT_README, encoding="utf-8")
    install_path = PACKAGE_DIR / "install.sh"
    install_path.write_text(INSTALL_SCRIPT, encoding="utf-8")
    install_path.chmod(0o755)

    archive_path = DIST / "edeka-promo-tool-linux.tar.gz"
    if archive_path.exists():
        archive_path.unlink()
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(PACKAGE_DIR, arcname=PACKAGE_DIR.name)

    print(f"SUCCESS: {binary}")
    print(f"PACKAGE: {archive_path}")


def main():
    build_frontend()
    pyinstaller = ensure_venv()
    build_binary(pyinstaller)
    package_linux()
    print("=== DONE ===")


if __name__ == "__main__":
    main()
