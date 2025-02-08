import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

# Import your handlers and utils
from handlers.start_handler import start_router
from handlers.quiz_session_handler import quiz_router
from config import quiz_data
from utils.db_utils import init_db

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize the bot and dispatcher
API_TOKEN = "7530128693:AAFcG6SiN2aU9paJuIvsdIskggQ9aTAW2m8"  # Replace with your bot's API token

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Load quiz data
if quiz_data:
    print("Quiz data loaded successfully.")
else:
    print("Failed to load quiz data.")

# Initialize the databases
init_db()

# Register routers
dp.include_router(start_router)
dp.include_router(quiz_router)

# ✅ Corrected polling method for aiogram 3.x
async def main():
    print("Bot is starting... 🚀")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Program terminated by user.")