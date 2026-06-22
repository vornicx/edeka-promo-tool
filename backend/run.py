import uvicorn
import webbrowser
import sys
from pathlib import Path
from app.main import app

if __name__ == "__main__":
    port = 8000
    url = f"http://localhost:{port}"

    if getattr(sys, "frozen", False):
        frontend_out = Path(sys._MEIPASS) / "frontend" / "out"
    else:
        frontend_out = Path(__file__).parent.parent / "frontend" / "out"

    if (frontend_out / "index.html").exists():
        if not (getattr(sys, "frozen", False) and sys.platform.startswith("linux")):
            print(f"  Abriendo {url} en el navegador...")
            webbrowser.open(url)
        else:
            print(f"  Abre la app en: {url}")
    else:
        print("  ADVERTENCIA: No se encontró frontend/out/. Construye el frontend primero:")
        print("    cd frontend && npm run build")

    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
