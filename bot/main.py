import asyncio
from urllib.parse import urlencode, urlsplit, urlunsplit

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from config import BOT_TOKEN, WEBAPP_URL

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

WELCOME = (
    "Assalomu alaykum! Buxoro Avto Magnat platformasiga xush kelibsiz. "
    "Avtomobilingiz uchun kerakli xizmatlar va ehtiyot qismlarni bir joydan toping."
)


def get_main_keyboard():
    url = urlsplit(WEBAPP_URL or "")
    if url.scheme != "https" or not url.hostname or "." not in url.hostname:
        return None

    buttons = (
        ("Avto Magnat ilovasini ochish", "home"),
        ("Xizmatlar", "services"),
        ("Mening buyurtmalarim", "orders"),
        ("Aloqa", "contact"),
    )
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, web_app=WebAppInfo(
            url=urlunsplit((url.scheme, url.netloc, url.path, urlencode({"view": view}), ""))
        ))] for label, view in buttons
    ])


@dp.message(CommandStart())
async def start_handler(message: Message):
    if message.chat.type != "private":
        await message.answer("Ilovani @BuxaraAvtoMagnatBot bilan shaxsiy chatda oching.")
        return
    keyboard = get_main_keyboard()
    await message.answer(WELCOME if keyboard else f"{WELCOME}\n\nIlova manzili hozircha sozlanmagan.",
                         reply_markup=keyboard)


@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer("/start orqali avtoservis, buyurtmalar va aloqa bo‘limlarini oching.")


async def main():
    async with bot:
        await bot.delete_webhook()
        await dp.start_polling(bot, close_bot_session=False)


if __name__ == "__main__":
    asyncio.run(main())
