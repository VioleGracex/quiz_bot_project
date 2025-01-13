import json
import logging
from telegram import Update
from telegram.ext import Application
from handlers.start_handler import setup_start_handlers
from handlers.quiz_session_handler import setup_session_handlers
from utils.db_utils import init_sessions_db, init_users_db  # Adjusted import



# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main() -> None:

    init_users_db()
    init_sessions_db()
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7530128693:AAFcG6SiN2aU9paJuIvsdIskggQ9aTAW2m8").build()

    # Set up all handlers for the bot
    setup_start_handlers(application)
    setup_session_handlers(application)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
