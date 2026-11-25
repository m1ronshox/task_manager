import hmac
import json
import time
from urllib.parse import parse_qsl

import jwt
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import User
from settings import ALLOW_LOCAL_DEV, BOT_TOKEN, JWT_SECRET, LOCAL_ORIGINS

INIT_DATA_MAX_AGE = 3600
JWT_ISSUER = "task-manager"
bearer = HTTPBearer(auto_error=False)


def verify_init_data(init_data: str, token: str) -> tuple[dict, int]:
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

        issued_at = int(fields["auth_date"])
        age = time.time() - issued_at
        if not -60 <= age <= INIT_DATA_MAX_AGE:
            raise ValueError
        user = json.loads(fields["user"])
        if not isinstance(user, dict) or type(user.get("id")) is not int:
            raise ValueError
        if not 0 < user["id"] < 2**52 or not isinstance(user.get("first_name"), str):
            raise ValueError
        if user.get("username") is not None and not isinstance(user["username"], str):
            raise ValueError
        if len(user["first_name"]) > 100 or len(user.get("username") or "") > 100:
            raise ValueError
        return user, issued_at
    except (KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired Telegram session") from None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> User:
    if credentials is not None:
        if JWT_SECRET:
            try:
                claims = jwt.decode(
                    credentials.credentials, JWT_SECRET, algorithms=["HS256"],
                    issuer=JWT_ISSUER, options={"require": ["sub", "iat", "exp", "iss"]},
                )
                user = db.get(User, int(claims["sub"]))
                if user is not None:
                    return user
            except (jwt.InvalidTokenError, ValueError):
                pass
        raise HTTPException(401, "Invalid or expired access token",
                            headers={"WWW-Authenticate": "Bearer"})
    if request.headers.get("authorization") is not None:
        raise HTTPException(401, "Expected a Bearer access token",
                            headers={"WWW-Authenticate": "Bearer"})
    if init_data is not None:
        identity, _ = telegram_identity(init_data)
    elif (
        ALLOW_LOCAL_DEV
        and request.client
        and request.client.host in ("127.0.0.1", "::1")
        and request.headers.get("origin") in LOCAL_ORIGINS
    ):
        identity = {"id": -1, "first_name": "Local development"}
    else:
        raise HTTPException(401, "Open Task Manager from Telegram")

    return get_or_create_user(db, identity)


def telegram_identity(init_data: str) -> tuple[dict, int]:
    if not BOT_TOKEN:
        raise HTTPException(503, "Telegram authentication is unavailable")
    return verify_init_data(init_data, BOT_TOKEN)


def get_or_create_user(db: Session, identity: dict) -> User:
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


def create_access_token(db: Session, init_data: str) -> str:
    if not JWT_SECRET:
        raise HTTPException(503, "JWT authentication is unavailable")

    identity, issued_at = telegram_identity(init_data)
    user = get_or_create_user(db, identity)
    return jwt.encode(
        {
            "sub": str(user.id),
            "iss": JWT_ISSUER,
            "iat": int(time.time()),
            "exp": issued_at + INIT_DATA_MAX_AGE,
        },
        JWT_SECRET,
        algorithm="HS256",
    )
