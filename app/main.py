import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from app.routers import auth, products, prices, stores, shopping_list, profile

load_dotenv()

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="PrecioJusto API",
    description="Grocery price comparison platform for Argentina",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(prices.router)
app.include_router(stores.router)
app.include_router(shopping_list.router)
app.include_router(profile.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "PrecioJusto API"}
