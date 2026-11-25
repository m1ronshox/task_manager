import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN sozlanmagan")

if os.getenv("RENDER") == "true":
    url = urlsplit(WEBAPP_URL or "")
    if url.scheme != "https" or not url.hostname or url.username is not None:
        raise ValueError("WEBAPP_URL uchun HTTPS manzil kiriting")
