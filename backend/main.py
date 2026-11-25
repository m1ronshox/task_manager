from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

import task
import users
from auth import create_access_token
from database import Base, engine, get_db
from schema import TelegramLogin, TokenResponse
from settings import FRONTEND_ORIGINS


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Telegram Task Manager API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Telegram-Init-Data"],
)

app.include_router(users.router)
app.include_router(task.router)


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
        "message": "Task Manager API is running",
    }
