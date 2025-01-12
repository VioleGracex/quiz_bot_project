import json
from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime
from utils.db_utils import create_quiz_session
from utils.time_utils import calculate_duration

async def start_quiz(update: Update, context: CallbackContext, quiz_name: str):
    session = create_quiz_session(update.effective_chat.id, quiz_name)
    context.user_data["quiz_session"] = session
    await ask_question(update, context, 0)

async def end_quiz(update: Update, context: CallbackContext):
    session = context.user_data.get("quiz_session", {})
    session["end_time"] = datetime.now()
    session["duration"] = calculate_duration(session["start_time"], session["end_time"])
    await update.message.reply_text(f"Quiz completed in {int(session['duration'])} seconds!")

async def ask_question(update: Update, context: CallbackContext, question_index: int):
    # Load question from JSON file
    quiz_name = context.user_data["quiz_session"]["quiz_name"]
    with open("data/questions.json", "r") as file:
        questions = json.load(file)["quizzes"][quiz_name]
    
    question = questions[question_index]
    options = "\n".join([f"{i + 1}. {opt}" for i, opt in enumerate(question["options"])])
    
    await update.message.reply_text(f"Question: {question['question']}\n{options}")
