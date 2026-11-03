import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).resolve().parent / 'campusdeal.db'}",
)


def _normalize_database_url(database_url: str) -> URL:
    url = make_url(database_url)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    if url.get_backend_name() == "postgresql" and not url.query.get("sslmode"):
        url = url.update_query_dict({"sslmode": "require"})
    return url


database_url = _normalize_database_url(DATABASE_URL)
engine_options: dict[str, object] = {"pool_pre_ping": True}
if database_url.get_backend_name() == "sqlite":
    engine_options["connect_args"] = {"check_same_thread": False}
elif database_url.get_backend_name() == "postgresql":
    engine_options.update(
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=300,
    )

engine = create_engine(database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
