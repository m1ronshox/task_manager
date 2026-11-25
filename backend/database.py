import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from sqlalchemy.engine import make_url

from settings import ON_RENDER

database_url = os.getenv("DATABASE_URL")
if ON_RENDER and not database_url:
    raise RuntimeError("DATABASE_URL is required on Render")

url = make_url(database_url or "sqlite:///./task_manager.db")
if url.drivername in ("postgres", "postgresql"):
    url = url.set(drivername="postgresql+psycopg")
if ON_RENDER and url.drivername != "postgresql+psycopg":
    raise RuntimeError("Render requires a PostgreSQL DATABASE_URL")

engine = create_engine(
    url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if url.get_backend_name() == "sqlite" else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
        