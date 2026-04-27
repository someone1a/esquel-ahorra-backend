from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
import os
from dotenv import load_dotenv
import logging

from app.database import engine, Base, create_tables, verify_database_connection
from app.routers import products, auth, locals
from app.models.token_blacklist import TokenBlacklist

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carga de variables de entorno
load_dotenv()

# Validar que existan variables de entorno críticas
required_env_vars = ["SECRET_KEY", "REFRESH_SECRET_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.warning(f"Variables de entorno faltantes: {missing_vars}")

# Crear la aplicación FastAPI
app = FastAPI(
    title="API de Esquel AHORRA",
    description="API para una webapp de comparacion de precios en esquel",
    version="2.0.0"
)

# Handler para errores de validación
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Error de validación: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Crear las tablas de la base de datos
try:
    create_tables()
    logger.info("Tablas de base de datos creadas/verificadas exitosamente")
except Exception as e:
    logger.error(f"Error al crear tablas: {str(e)}")

# Verificar conexión a BD
try:
    if verify_database_connection():
        logger.info("✓ Conexión a base de datos establecida")
    else:
        logger.error("✗ No se pudo establecer conexión a base de datos")
except Exception as e:
    logger.error(f"Error al verificar conexión: {str(e)}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8081","https://esquel-ahorra.online"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Incluir routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(locals.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la api de esquel AHORRA"}

@app.get("/health-check")
def health_check():
    try:
        if verify_database_connection():
            return {"status": "ok", "message": "Estoy vivo!", "database": "connected"}
        else:
            return {"status": "warning", "message": "Estoy vivo pero sin conexión a BD", "database": "disconnected"}
    except Exception as e:
        logger.error(f"Error en health-check: {str(e)}")
        return {"status": "warning", "message": "Error verificando BD", "database": "error"}

# Obtener el puerto de la variable de entorno o usar el predeterminado
port = int(os.getenv("PORT", "8000"))

# Para despliegue
if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Permitir puerto por argumento de línea de comandos
    if len(sys.argv) > 2 and sys.argv[1] == "--port":
        current_port = int(sys.argv[2])
    else:
        current_port = port
        
    uvicorn.run(app, host="0.0.0.0", port=current_port)
