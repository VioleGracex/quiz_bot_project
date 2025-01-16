import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from handlers.json_functions import load_quiz_data
from handlers.start_handler import setup_start_handlers
from handlers.quiz_session_handler import setup_session_handlers
from utils.db_utils import init_db
from config import quiz_data

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid logging all GET and POST requests
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message with instructions to the user."""
    help_text = (
        "Welcome to the Quiz Bot! Here are some useful commands:\n\n"
        "/start - Start a new session\n"
        "/quiz_start - Start a new quiz session\n"
        "/help - Get this help message\n"
        "You can also interact with the bot through buttons in the quiz interface.\n\n"
        "Good luck, and enjoy the quiz!"
    )
    await update.message.reply_text(help_text)

def main() -> None:
    # Initialize the databases
    #load_quiz_data()
    if quiz_data:
        print("Quiz data loaded successfully.")
    else:
        print("Failed to load quiz data.")

    # Create the Application and pass it your bot's token.
    token = "7530128693:AAFcG6SiN2aU9paJuIvsdIskggQ9aTAW2m8"  # Make sure to keep the token safe
    application = Application.builder().token(token).build()
    

    # Set up all handlers for the bot
    application.add_handler(CommandHandler("help", help))
    setup_start_handlers(application)
    
    setup_session_handlers(application)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
