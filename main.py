from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
import os
from dotenv import load_dotenv
import logging

from app.database import verify_database_connection
from app.routers import products, auth, locals, corrections
from app.models.token_blacklist import TokenBlacklist

logger = logging.getLogger(__name__)

class BodyTooLarge(Exception):
    pass

class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_size: int = 1024 * 1024):
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope.get("headers", [])}
        content_length = headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_size:
                    response = JSONResponse(status_code=413, content={"detail": "Request too large"})
                    await response(scope, receive, send)
                    return
            except ValueError:
                pass

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                received += len(body)
                if received > self.max_size:
                    raise BodyTooLarge()
            return message

        try:
            await self.app(scope, limited_receive, send)
        except BodyTooLarge:
            response = JSONResponse(status_code=413, content={"detail": "Request too large"})
            await response(scope, receive, send)

# Carga de variables de entorno
load_dotenv()

# Validar que existan variables de entorno críticas
required_env_vars = ["SECRET_KEY", "REFRESH_SECRET_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Variables de entorno faltantes: {missing_vars}")
    raise ValueError(f"Required environment variables are missing: {missing_vars}")

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

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# Verificar conexión a BD
try:
    if verify_database_connection():
        logger.info("✓ Conexión a base de datos establecida")
    else:
        logger.error("✗ No se pudo establecer conexión a base de datos")
except Exception as e:
    logger.error(f"Error al verificar conexión: {str(e)}")

# Agregar middleware de límite de tamaño de request
app.add_middleware(RequestSizeLimitMiddleware, max_size=1024 * 1024)

# Configurar CORS con métodos y headers específicos
cors_origins_env = os.getenv("CORS_ORIGINS")
allow_origins = ["https://esquel-ahorra.online"]
if cors_origins_env:
    allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"]
)

# Incluir routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(locals.router)
app.include_router(corrections.router)

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
