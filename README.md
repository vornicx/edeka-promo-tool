# EDEKA Mühlenbein Promo Tool

Herramienta de creación de promociones con IA para EDEKA Mühlenbein.

## Requisitos

- Python 3.12+
- Node.js 18+
- API key de OpenRouter (https://openrouter.ai)

## Instalación rápida

```bash
# 1. Configurar API key
echo "OPENROUTER_API_KEY=tu_key_aqui" > backend/.env

# 2. Instalar dependencias
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 3. Ejecutar
cd .. && bash start.sh
```

## URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Documentación API: http://localhost:8000/docs

## Flujo de uso

1. El usuario llena el formulario con los datos del producto
2. La IA genera 3 direcciones creativas
3. El usuario elige 1 dirección
4. El sistema compone la promoción sobre una plantilla
5. Se puede exportar en 4 formatos: Post, Story, A4, A5

## Estructura del proyecto

```
edeka-promo-tool/
├── backend/          # Python FastAPI
├── frontend/         # Next.js + TypeScript
├── start.sh          # Script de inicio
└── README.md
```

## Tecnologías

- **Backend:** Python 3.12, FastAPI, Pillow
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS
- **IA:** OpenRouter (GPT-4o-mini por defecto)
- **Fondos:** Generados gradiente por sección
- **Tipografía:** Open Sans
