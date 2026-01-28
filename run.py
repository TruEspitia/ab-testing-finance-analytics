"""
Script para iniciar la aplicación FastAPI
"""
import uvicorn
from pathlib import Path
import sys

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

if __name__ == "__main__":
    print("🚀 Iniciando servidor FastAPI...")
    print("📍 URL: http://localhost:8000")
    print("📚 Documentación API: http://localhost:8000/docs")
    print("\nPresiona Ctrl+C para detener el servidor\n")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
