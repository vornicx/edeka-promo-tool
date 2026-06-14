import uvicorn
import webbrowser
from pathlib import Path

if __name__ == "__main__":
    port = 8000
    url = f"http://localhost:{port}"

    frontend_out = Path(__file__).parent.parent / "frontend" / "out"
    if (frontend_out / "index.html").exists():
        print(f"  Abriendo {url} en el navegador...")
        webbrowser.open(url)
    else:
        print("  ADVERTENCIA: No se encontró frontend/out/. Construye el frontend primero:")
        print("    cd frontend && npm run build")

    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
