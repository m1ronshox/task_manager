import os

from fastapi import FastAPI
from auth import LOCAL_ORIGINS

from database import engine, Base
import models

import task
import users

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Telegram Task Manager API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        *LOCAL_ORIGINS,
        *(origin.strip() for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
          if origin.strip()),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(task.router)


@app.get("/")
def home():
    return {
        "status": "success",
        "message": "Task Manager API is running"
    }
