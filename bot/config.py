
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

WEBHOOK_PATH = "/telegram/webhook"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN sozlanmagan")

WEBHOOK_URL = (
    WEBHOOK_BASE_URL.rstrip("/")
    + WEBHOOK_PATH
    if WEBHOOK_BASE_URL else None
)
