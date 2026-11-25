import asyncio
from urllib.parse import urlsplit

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)

from config import BOT_TOKEN, WEBAPP_URL


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_main_keyboard():
    url = urlsplit(WEBAPP_URL or "")
    if url.scheme != "https" or not url.hostname or "." not in url.hostname:
        return None

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Open Task Manager",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL
                    )
                )
            ]
        ]
    )

    return keyboard


@dp.message(CommandStart())
async def start_handler(message: Message):

    user = message.from_user
    keyboard = get_main_keyboard() if message.chat.type == "private" else None
    instructions = (
        "Kundalik vazifalaringizni boshqarish uchun quyidagi tugmani bosing."
        if keyboard
        else "Task Manager uchun HTTPS manzil hali sozlanmagan. /help orqali yordam oling."
    )

    if message.chat.type != "private":
        instructions = "Task Manager ilovasini bot bilan shaxsiy chatda oching."

    await message.answer(
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "Task Manager ilovasiga xush kelibsiz.\n\n"
        f"{instructions}",
        reply_markup=keyboard
    )


@dp.message(Command("help"))
async def help_handler(message: Message):

    await message.answer(
        "Task Manager bot yordam bo'limi.\n\n"
        "/start - Ilovani ochish\n"
        "/help - Yordam"
    )


if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
