# EDEKA Mühlenbein Promo Tool

Herramienta web de creación de promociones con IA para EDEKA Mühlenbein.

## Despliegue web con login

El despliegue público sirve la landing en `/` y protege el estudio web en `/studio` con contraseña. La landing habla de la herramienta y lleva a `/login?next=/studio`; no debe presentarse como descarga desktop.

Variables en Vercel:

- `PROMO_LOGIN_PASSWORD`: contraseña de acceso para el cliente.
- `PROMO_AUTH_SECRET`: secreto largo para firmar la cookie de sesión. Si no se define, se usa la contraseña como secreto de firma.

La sesión dura 12 horas. Para desarrollo local puedes poner esas variables en `frontend/.env.local`.

## Uso del cliente

El cliente no necesita instalar Python ni Node.js si recibe el `.exe` generado.

1. Ejecutar `edeka-promo-tool.exe`
2. Abrir el apartado **Ajustes IA**
3. Pegar su API key
4. Elegir proveedor/modelo
5. Guardar y crear promociones

La key se guarda localmente en el equipo del cliente:

- Windows: `%APPDATA%\EDEKA Promo Tool\settings.json`
- Linux: `~/.config/edeka-promo-tool/settings.json`
- macOS: `~/Library/Application Support/EDEKA Promo Tool/settings.json`

## Generar el .exe

Requisitos de build:

- Docker
- Node.js 18+

```bash
python3 build_desktop.py
```

El ejecutable queda en:

```bash
dist/edeka-promo-tool.exe
```

Ese archivo se puede enviar al cliente para descargar y ejecutar.

## Generar instalador Linux

Requisitos de build:

- Python 3.12+
- Node.js 18+

```bash
python3 build_linux.py
```

El paquete queda en:

```bash
dist/edeka-promo-tool-linux.tar.gz
```

Para instalarlo en Linux:

```bash
tar -xzf dist/edeka-promo-tool-linux.tar.gz -C /tmp
cd /tmp/edeka-promo-tool-linux
./install.sh
```

## Desarrollo local

Requisitos:

- Python 3.12+
- Node.js 18+

## Instalación rápida

```bash
# 1. Instalar dependencias
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 2. Ejecutar
cd .. && bash start.sh
```

La API key se configura desde el botón **Ajustes IA** en la interfaz.

## URLs

- Frontend: http://localhost:3001
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
- **IA:** OpenRouter por defecto, compatible con APIs estilo OpenAI
- **Fondos:** Generados gradiente por sección
- **Tipografía de piezas exportadas:** Open Sans
