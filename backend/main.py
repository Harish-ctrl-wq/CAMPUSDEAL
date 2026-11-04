from contextlib import asynccontextmanager
import json
import os
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import Base, SessionLocal, engine
from models import Product
from routes import analytics, products, recommendations

SAMPLE_DATA = Path(__file__).resolve().parent / "data" / "sample_products.json"


def _get_cors_origins() -> list[str]:
    """Get CORS origins from environment variable.
    
    If CORS_ORIGINS is set, use only explicitly configured origins.
    If unset or empty, use localhost development defaults.
    Never uses wildcard origins.
    """
    cors_origins = os.getenv("CORS_ORIGINS", "")
    origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    
    if not origins:
        # Local development defaults only when CORS_ORIGINS is not configured
        origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    return origins


@asynccontextmanager
async def lifespan(_: FastAPI):
    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(Product).count() == 0:
            samples = json.loads(SAMPLE_DATA.read_text(encoding="utf-8"))
            db.add_all(Product(**record) for record in samples)
            db.commit()
    yield


app = FastAPI(title="CampusDeal API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(products.router)
app.include_router(recommendations.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"name": "CampusDeal API", "docs": "/docs", "status": "ok"}


@app.get("/health")
def health():
    """Lightweight health check - returns 200 if app is running."""
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response):
    """Readiness check - verifies database connectivity."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        response.status_code = 503
        return {"status": "not ready", "database": "disconnected"}
