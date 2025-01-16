import os
from dotenv import load_dotenv

from handlers.json_functions import load_quiz_data

load_dotenv()
BOT_TOKEN = os.getenv("7530128693:AAFcG6SiN2aU9paJuIvsdIskggQ9aTAW2m8")
quiz_data = load_quiz_data()
