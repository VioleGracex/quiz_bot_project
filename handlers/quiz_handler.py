import json
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from datetime import datetime
from handlers.menu_handler import show_quiz_menu
from models.quiz_model import QuizSession
from utils.db_utils import create_quiz_session
from utils.time_utils import calculate_duration

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def handle_quiz_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    chat_id = update.effective_chat.id

    logging.info(f"Quiz selection received: {callback_data} from chat_id: {chat_id}")
    print(f"Quiz selection received: {callback_data}")

    if callback_data.startswith("quiz_"):
        quiz_name = callback_data.split('_', 1)[1]
        logging.info(f"Selected quiz: {quiz_name}")
        
        quiz_session = QuizSession(user_id=chat_id, quiz_name=quiz_name)
        context.user_data["quiz_session"] = quiz_session

        await query.message.reply_text(f"You chose the {quiz_name} quiz.")
        await ask_question(update, context, 0)
    elif callback_data == "end":
        if "quiz_session" in context.user_data:
            del context.user_data["quiz_session"]
            await query.message.reply_text("The quiz has been ended. Thank you for participating!")
        else:
            await query.message.reply_text("No quiz session was started.")

async def ask_question(update: Update, context: CallbackContext, question_index: int):
    quiz_session = context.user_data.get("quiz_session")

    if not quiz_session:
        await update.callback_query.message.reply_text("No quiz session found. Please start a quiz first.")
        return

    quiz_name = quiz_session.quiz_name
    logging.debug(f"Asking question {question_index} for quiz: {quiz_name}")

    try:
        with open("data/questions.json", "r") as file:
            questions = json.load(file)["quizzes"].get(quiz_name, [])

        if question_index >= len(questions):
            await end_quiz(update, context)
            return

        question = questions[question_index]
        options = question.get("options", [])
        keyboard = [[InlineKeyboardButton(opt, callback_data=f"answer_{i}")] for i, opt in enumerate(options)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        logging.info(f"Question: {question['question']} with options: {options}")
        await update.callback_query.message.reply_text(f"Question: {question['question']}", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in ask_question: {e}")
        await update.callback_query.message.reply_text(f"An error occurred: {e}")

async def handle_answer(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    quiz_session = context.user_data.get("quiz_session")
    if not quiz_session:
        await query.message.reply_text("No quiz session found. Please start a quiz.")
        return

    logging.info(f"Handling answer for question index: {quiz_session.current_question_index}")
    print(f"User answered: {query.data}")

    try:
        with open("data/questions.json", "r") as file:
            questions = json.load(file)["quizzes"].get(quiz_session.quiz_name, [])

        if quiz_session.current_question_index < len(questions):
            correct_answer_index = questions[quiz_session.current_question_index].get("answer", -1)
            user_answer_index = int(query.data.split('_')[1])

            if user_answer_index == correct_answer_index:
                quiz_session.score += 1
                logging.info("User answered correctly.")
                await update.message.reply_text("Correct!")
            else:
                correct_option = questions[quiz_session.current_question_index]['options'][correct_answer_index]
                logging.info("User answered incorrectly.")
                await query.message.reply_text(f"Incorrect. The correct answer was: {correct_option}")

            quiz_session.current_question_index += 1
            if quiz_session.current_question_index < len(questions):
                await ask_question(update, context, quiz_session.current_question_index)
            else:
                await show_score_and_menu(update, context)
    except Exception as e:
        logging.error(f"Error in handle_answer: {e}")
        await query.message.reply_text(f"An error occurred: {e}")

async def show_score_and_menu(update: Update, context: CallbackContext):
    quiz_session = context.user_data.get("quiz_session")
    if quiz_session:
        score_message = f"Quiz finished! Your score: {quiz_session.score} / {quiz_session.current_question_index}"
        logging.info(score_message)
        await update.callback_query.message.reply_text(score_message)
        context.user_data.pop("quiz_session", None)
    await show_quiz_menu(update, context)

async def end_quiz(update: Update, context: CallbackContext):
    quiz_session = context.user_data.get("quiz_session")
    if not quiz_session:
        await update.callback_query.message.reply_text("Quiz session not found.")
        return

    score = quiz_session.score
    total_questions = quiz_session.current_question_index
    logging.info(f"Ending quiz. Score: {score}/{total_questions}")

    await update.callback_query.message.reply_text(f"Quiz completed! Your score is {score} out of {total_questions}.")
    del context.user_data["quiz_session"]
    await update.callback_query.message.reply_text("Returning to the quiz menu.")
