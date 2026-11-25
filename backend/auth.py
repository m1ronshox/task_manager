import hmac
import json
import os
import time
from pathlib import Path
from urllib.parse import parse_qsl

from dotenv import dotenv_values
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import User


LOCAL_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")
BOT_TOKEN = os.getenv("BOT_TOKEN") or dotenv_values(
    Path(__file__).resolve().parent.parent / "bot" / ".env"
).get("BOT_TOKEN")
ALLOW_LOCAL_DEV = os.getenv("ALLOW_LOCAL_DEV") == "1"
INIT_DATA_MAX_AGE = 3600


def verify_init_data(init_data: str, token: str) -> dict:
    try:
        pairs = parse_qsl(
            init_data, keep_blank_values=True, strict_parsing=True,
            max_num_fields=32, errors="strict",
        )
        fields = dict(pairs)
        received_hash = fields.pop("hash").encode("ascii")
        if len(fields) + 1 != len(pairs):
            raise ValueError
        check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
        secret = hmac.digest(b"WebAppData", token.encode(), "sha256")
        expected_hash = hmac.digest(secret, check_string.encode(), "sha256").hex()
        if not hmac.compare_digest(expected_hash.encode(), received_hash):
            raise ValueError

        age = time.time() - int(fields["auth_date"])
        if not -60 <= age <= INIT_DATA_MAX_AGE:
            raise ValueError
        user = json.loads(fields["user"])
        if not isinstance(user, dict) or type(user.get("id")) is not int:
            raise ValueError
        if not 0 < user["id"] < 2**52 or not isinstance(user.get("first_name"), str):
            raise ValueError
        if user.get("username") is not None and not isinstance(user["username"], str):
            raise ValueError
        return user
    except (KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired Telegram session") from None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
) -> User:
    if init_data is not None:
        if not BOT_TOKEN:
            raise HTTPException(503, "Telegram authentication is unavailable")
        identity = verify_init_data(init_data, BOT_TOKEN)
    elif (
        ALLOW_LOCAL_DEV
        and request.client
        and request.client.host in ("127.0.0.1", "::1")
        and request.headers.get("origin") in LOCAL_ORIGINS
    ):
        identity = {"id": -1, "first_name": "Local development"}
    else:
        raise HTTPException(401, "Open Task Manager from Telegram")

    users = db.query(User).filter(User.telegram_id == identity["id"])
    user = users.first()
    if user is not None:
        return user

    user = User(
        telegram_id=identity["id"],
        first_name=identity["first_name"],
        username=identity.get("username"),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = users.first()
        if existing is None:
            raise
        return existing
    db.refresh(user)
    return user
