from contextlib import asynccontextmanager
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, SessionLocal, engine
from models import Product
from routes import analytics, products, recommendations

SAMPLE_DATA = Path(__file__).resolve().parent / "data" / "sample_products.json"


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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
