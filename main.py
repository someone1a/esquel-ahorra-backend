from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.database import engine, Base, create_tables
from app.routers import products, auth, locals

# Carga de variables de entorno
load_dotenv()

# Crear la aplicación FastAPI
app = FastAPI(
    title="API de Esquel AHORRA",
    description="API para una webapp de comparacion de precios en esquel",
    version="2.0.0"
)

# Crear las tablas de la base de datos
create_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://esquel-ahorra.online/"],
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
    return {"status": "ok", "message": "Estoy vivo!"}

# Obtener el puerto de la variable de entorno o usar el predeterminado
port = int(os.getenv("PORT", "8000"))

# Para despliegue
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
