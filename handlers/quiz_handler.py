import json
from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime
from utils.db_utils import create_quiz_session
from utils.time_utils import calculate_duration

async def handle_quiz_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    callback_data = query.data  # The data sent by the inline button
    chat_id = update.effective_chat.id  # Chat ID of the user

    # If a quiz is selected, store the quiz name in the context
    if callback_data.startswith("quiz_"):
        quiz_name = callback_data.split('_', 1)[1]  # Extract quiz name
        
        # Store the selected quiz name in context.user_data
        context.user_data["selected_quiz"] = quiz_name
        
        # Display the chosen quiz to the user
        await query.message.reply_text(f"You chose the {quiz_name} quiz.")
    
    # If "end" is selected, end the quiz session and clear context data
    elif callback_data == "end":
        # Check if a quiz session exists and clear it
        if "selected_quiz" in context.user_data:
            del context.user_data["selected_quiz"]
            await query.message.reply_text("The quiz has been ended. Thank you for participating!")
        else:
            await query.message.reply_text("No quiz session was started.")

async def end_quiz(update: Update, context: CallbackContext):
    session = context.user_data.get("quiz_session", None)
    
    if session is None:
        await update.message.reply_text("Quiz session not found. Please start the quiz first.")
        return

    session["end_time"] = datetime.now()
    session["duration"] = calculate_duration(session["start_time"], session["end_time"])
    await update.message.reply_text(f"Quiz completed in {int(session['duration'])} seconds!")

async def ask_question(update: Update, context: CallbackContext, question_index: int):
    # Ensure quiz session exists
    quiz_session = context.user_data.get("quiz_session", None)
    
    if not quiz_session:
        await update.message.reply_text("No quiz session found. Please start a quiz first.")
        return

    quiz_name = quiz_session.get("quiz_name", None)
    if not quiz_name:
        await update.message.reply_text("Quiz name is missing. Please start the quiz again.")
        return
    
    # Load question from JSON file
    try:
        with open("data/questions.json", "r") as file:
            questions = json.load(file)["quizzes"].get(quiz_name, [])
        
        if not questions:
            await update.message.reply_text(f"No questions found for quiz: {quiz_name}.")
            return
        
        question = questions[question_index]
        options = "\n".join([f"{i + 1}. {opt}" for i, opt in enumerate(question["options"])])
        await update.message.reply_text(f"Question: {question['question']}\n{options}")
    
    except FileNotFoundError:
        await update.message.reply_text("Error: Question file not found. Please try again later.")
    except json.JSONDecodeError:
        await update.message.reply_text("Error: There was an issue reading the question file. Please try again later.")
