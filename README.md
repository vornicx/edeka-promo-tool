# EDEKA Mühlenbein Promo Tool

Herramienta web de creación de promociones con IA para EDEKA Mühlenbein.

## Despliegue web con login

El despliegue público sirve la landing en `/` y protege el estudio web en `/studio` con contraseña. La landing lleva a `/login?next=/studio`; el resto de páginas y APIs quedan detrás de la cookie de sesión.

Variables en Vercel:

- `PROMO_LOGIN_PASSWORD`: contraseña de acceso para el cliente.
- `PROMO_AUTH_SECRET`: secreto largo para firmar la cookie de sesión. Si no se define, se usa la contraseña como secreto de firma.

La sesión dura 12 horas. Para desarrollo local puedes poner esas variables en `frontend/.env.local`.

La API de ajustes nunca devuelve el API key completo al navegador: solo indica si existe y muestra una versión enmascarada.

## Persistencia en Railway

Los datos mutables del servicio se guardan bajo `PROMO_DATA_DIR`. En Railway, si no se define la variable, el valor por defecto es:

```text
/data/edeka-promo-tool
```

Para que ajustes de IA, productos subidos y recursos generados sobrevivan a reinicios y despliegues, monta un **Railway Volume en `/data`**. También puedes definir `PROMO_DATA_DIR` si prefieres otro punto de montaje.

Para limitar el backend a los frontends esperados puedes usar:

```text
PROMO_ALLOWED_ORIGINS=https://edekamuhlenbein.vercel.app
```

Se pueden añadir varios orígenes separados por comas.

## Uso del cliente

El flujo habitual está pensado para ser rápido: producto, precio, periodo, imagen y generación. El formulario conserva opciones de diseño, formatos, campañas múltiples y KI-Design cuando hacen falta, sin cambiar el flujo básico que ya usa el cliente.

El cliente no necesita instalar Python ni Node.js si recibe el `.exe` generado.

1. Ejecutar `edeka-promo-tool.exe`
2. Abrir el apartado **Ajustes IA** si quiere usar IA
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

## Calidad

El workflow `Quality checks` valida en cada pull request:

- build de producción del frontend Next.js;
- arranque del backend;
- que el API key no se exponga;
- creación de una promoción local;
- composición y selección de variantes;
- recuperación de la imagen generada;
- exportación final.

También se ejecuta al hacer push a `main`.

## URLs

- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- Documentación API: http://localhost:8000/docs

## Flujo de uso

1. El usuario elige el tipo de creación: Einzelangebot (plantillas), Wochenangebote (2-6 productos en un cartel tipo folleto) o KI-Design
2. Llena el formulario con los datos del producto/evento
3. El sistema compone 3 variantes de diseño y el usuario elige una visualmente
4. Puede ajustar el briefing sin perder datos ("Anpassen") o recuperar una promoción anterior desde "Meine Aktionen" (historial local)
5. Exporta el formato elegido en PNG 4K, todos los formatos en un ZIP, o PDF a 300 dpi para imprimir A4/A5; en móvil puede compartir directamente

## Estructura del proyecto

```text
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
