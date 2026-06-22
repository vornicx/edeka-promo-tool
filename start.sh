#!/bin/bash
# EDEKA Mühlenbein Promo Tool - Startup Script

set -euo pipefail

echo "=== EDEKA Mühlenbein Promo Tool ==="
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Detectar Python del venv o usar python3
if [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
    PYTHON="$BACKEND_DIR/.venv/bin/python"
else
    PYTHON="python3"
fi

echo "Python del backend: $PYTHON"

# Start backend
echo "Iniciando backend en http://localhost:8000..."
cd "$BACKEND_DIR"
"$PYTHON" run.py &
BACKEND_PID=$!

# Esperar a que el backend responda health
for _ in $(seq 1 40); do
    if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
        break
    fi
    sleep 0.25
done

# Start frontend
echo "Iniciando frontend en http://localhost:3001..."
cd "$FRONTEND_DIR"
NEXT_PUBLIC_API_URL=http://localhost:8000/api/promo npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3001"
echo "API Docs: http://localhost:8000/docs"
echo "Ajustes IA: botón 'Ajustes IA' dentro de la app"
echo ""
echo "Presiona Ctrl+C para detener ambos servicios"

cleanup() {
    echo ""
    echo "Deteniendo servicios..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    exit
}
trap cleanup INT TERM
wait
