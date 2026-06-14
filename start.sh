#!/bin/bash
# EDEKA Mühlenbein Promo Tool - Startup Script

echo "=== EDEKA Mühlenbein Promo Tool ==="
echo ""

# Check for env.local file
if [ ! -f backend/env.local ]; then
    echo "ERROR: backend/env.local no encontrado."
    echo "Crea el archivo con tu API key de OpenRouter:"
    echo '  echo "OPENROUTER_API_KEY=tu_key_aqui" > backend/env.local'
    exit 1
fi

# Start backend
echo "Iniciando backend en http://localhost:8000..."
cd backend && python3 run.py &
BACKEND_PID=$!

# Start frontend
echo "Iniciando frontend en http://localhost:3001..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3001"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Presiona Ctrl+C para detener ambos servicios"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
