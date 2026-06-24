#!/usr/bin/env bash
# Instalador interactivo de EDEKA Promo Tool.
# Doble clic (o ./instalar.sh) y elige tu plataforma.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST="$ROOT/dist"
URL="http://127.0.0.1:8000"

echo "============================================"
echo "   EDEKA Mühlenbein – Promo Studio"
echo "   Instalador"
echo "============================================"
echo ""
echo "¿En qué sistema quieres instalarlo?"
echo "  1) Linux  (este equipo – instala y abre la app)"
echo "  2) Windows (prepara el paquete para llevarlo a un PC Windows)"
echo "  3) Mac     (prepara el paquete para llevarlo a un Mac)"
echo ""
read -rp "Opción [1-3]: " OPCION

prepara_paquete() {
  local archivo="$1" nombre="$2"
  if [ ! -f "$DIST/$archivo" ]; then
    echo ""
    echo "  No encuentro $archivo en dist/."
    echo "  Genera el build o descárgalo desde GitHub Actions:"
    echo "  https://github.com/vornicx/edeka-promo-tool/actions"
    exit 1
  fi
  local destino="$HOME/Escritorio/EDEKA-Promo-$nombre"
  mkdir -p "$destino"
  cp "$DIST/$archivo" "$destino/"
  cp "$ROOT/ANLEITUNG.md" "$destino/" 2>/dev/null || true
  echo ""
  echo "  Listo. Copia esta carpeta al equipo $nombre:"
  echo "    $destino"
  echo "  Dentro está el instalador y la guía (ANLEITUNG.md)."
}

case "$OPCION" in
  1)
    echo ""
    echo ">> Instalando en Linux..."
    if [ ! -f "$DIST/edeka-promo-tool-linux/install.sh" ]; then
      echo "  No encuentro el paquete Linux en dist/. Ejecuta antes: python3 build_linux.py"
      exit 1
    fi
    fuser -k 8000/tcp 2>/dev/null || true
    sleep 1
    bash "$DIST/edeka-promo-tool-linux/install.sh"
    echo ""
    echo ">> Abriendo la app..."
    nohup "$HOME/.local/bin/edeka-promo-tool" >/dev/null 2>&1 &
    sleep 6
    if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true; fi
    echo ""
    echo "  Instalado. La app está en tu menú como 'EDEKA Promo Tool'."
    echo "  También se abre en: $URL"
    ;;
  2) prepara_paquete "edeka-promo-tool-windows.zip" "Windows" ;;
  3) prepara_paquete "edeka-promo-tool-mac.zip" "Mac" ;;
  *) echo "Opción no válida."; exit 1 ;;
esac
