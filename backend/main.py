from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

import automotive
import task
import users
from auth import create_access_token
from database import get_db
from rate_limit import RateLimit
from schema import TelegramLogin, TokenResponse
from settings import FRONTEND_ORIGINS


@asynccontextmanager
async def lifespan(app: FastAPI):
    command.upgrade(Config(str(Path(__file__).with_name('alembic.ini'))), 'head')
    yield


app = FastAPI(
    title="Buxoro Avto Magnat API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RateLimit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Telegram-Init-Data"],
)

app.include_router(users.router)
app.include_router(task.router)
app.include_router(automotive.router)


@app.post("/api/auth/telegram", response_model=TokenResponse)
def login(data: TelegramLogin, db: Session = Depends(get_db)):
    return TokenResponse(access_token=create_access_token(db, data.init_data))


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/")
def home():
    return {
        "status": "success",
        "message": "Buxoro Avto Magnat API is running",
    }
