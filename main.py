import json
import logging
from telegram import Update
from telegram.ext import Application
from handlers.start_handler import setup_start_handlers
from handlers.quiz_session_handler import setup_session_handlers
from utils.db_utils import init_sessions_db, init_users_db  


# Sample JSON data structure for quiz categories and questions
quiz_data = {
    "categories": [
        {
            "name": "Science",
            "questions": [
                {
                    "question": "What is the chemical symbol for water?",
                    "answers": ["H2O", "CO2", "O2", "H2"],
                    "correct_answer_index": 0
                },
                {
                    "question": "What planet is known as the Red Planet?",
                    "answers": ["Mars", "Earth", "Jupiter", "Venus"],
                    "correct_answer_index": 0
                }
            ]
        },
        {
            "name": "History",
            "questions": [
                {
                    "question": "Who was the first president of the United States?",
                    "answers": ["George Washington", "Abraham Lincoln", "Thomas Jefferson", "John Adams"],
                    "correct_answer_index": 0
                },
                {
                    "question": "What year did World War II end?",
                    "answers": ["1945", "1939", "1950", "1918"],
                    "correct_answer_index": 0
                }
            ]
        }
    ]
}
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main() -> None:
    """Run the bot."""
    with open('data/quiz_data.json', 'w') as file:
        json.dump(quiz_data, file)

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
