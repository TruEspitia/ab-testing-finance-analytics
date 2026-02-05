"""
Script para iniciar la aplicación FastAPI con auto-apertura del navegador
"""
import uvicorn
from pathlib import Path
import sys
import webbrowser
import threading
import time

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))


def open_browser(url: str, delay: float = 1.5):
    """
    Abre el navegador después de un delay para asegurar que el servidor esté listo
    
    Args:
        url: URL a abrir
        delay: Tiempo de espera en segundos antes de abrir el navegador
    """
    time.sleep(delay)
    print(f"🌐 Abriendo navegador en {url}...")
    webbrowser.open(url)


if __name__ == "__main__":
    # Configuración del servidor
    host = "localhost"
    port = 8080
    url = f"http://{host}:{port}"
    
    print("=" * 60)
    print("🚀 Iniciando A/B Testing Finance Analytics")
    print("=" * 60)
    print(f"📍 URL de la aplicación: {url}")
    print(f"📚 Documentación API: {url}/docs")
    print(f"🔧 API Endpoints: {url}/api/datasets")
    print("=" * 60)
    print("💡 El navegador se abrirá automáticamente en unos segundos...")
    print("⚠️  Presiona Ctrl+C para detener el servidor")
    print("=" * 60)
    print()
    
    # Iniciar thread para abrir el navegador
    browser_thread = threading.Thread(
        target=open_browser,
        args=(url,),
        daemon=True
    )
    browser_thread.start()
    
    # Iniciar servidor
    try:
        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Servidor detenido. ¡Hasta pronto!")
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
        sys.exit(1)

