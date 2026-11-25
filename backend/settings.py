import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"))

ON_RENDER = os.getenv("RENDER") == "true"
LOCAL_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")
ALLOW_LOCAL_DEV = not ON_RENDER and os.getenv("ALLOW_LOCAL_DEV") == "1"
BOT_TOKEN = os.getenv("BOT_TOKEN")
JWT_SECRET = os.getenv("JWT_SECRET")

if ON_RENDER and not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required on Render")
if (ON_RENDER or JWT_SECRET) and len(JWT_SECRET or "") < 32:
    raise RuntimeError("JWT_SECRET must be at least 32 characters")

FRONTEND_ORIGINS = []
for value in os.getenv("FRONTEND_ORIGINS", "").split(","):
    origin = value.strip()
    if not origin:
        continue
    url = urlsplit(origin)
    if (
        url.scheme != "https"
        or not url.hostname
        or url.username is not None
        or "*" in origin
        or origin != f"https://{url.netloc}"
    ):
        raise RuntimeError("FRONTEND_ORIGINS must contain exact HTTPS origins")
    FRONTEND_ORIGINS.append(origin)

if ALLOW_LOCAL_DEV:
    FRONTEND_ORIGINS.extend(LOCAL_ORIGINS)
