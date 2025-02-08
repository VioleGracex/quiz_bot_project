import logging
import random
from datetime import datetime
from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import quiz_data
from utils.db_utils import QuizSession, save_session_to_user
from handlers.json_functions import load_quiz_data
from handlers.quiz_keyboards import show_start_game_keyboard, show_end_game_keyboard, show_other_categories_keyboard

quiz_router = Router()

# Initialize a global variable to store quiz data
if quiz_data is None:
    load_quiz_data()

def shuffle_loaded_json():
    global quiz_data
    if quiz_data is None:
        quiz_data = load_quiz_data()  # Load quiz data from your JSON function
        
    for category in quiz_data['categories']:
        random.shuffle(category['questions'])

@quiz_router.message(Command("quiz_start"))
async def quiz_start(message: Message, state: FSMContext):
    if quiz_data is None:
        shuffle_loaded_json()
        
    try:
        await show_start_game_keyboard(message, state)
        await state.update_data(quiz_in_progress=False, score=0, current_question_index=0)
    except Exception as e:
        await message.answer("There was an issue starting the quiz. Please contact support.")
        logging.error(f"Error in quiz_start: {e}")

@quiz_router.callback_query(F.data == "continue_quiz")
async def continue_quiz(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text("Continuing your quiz session...")

    keyboard = [
        [
            InlineKeyboardButton(text="Continue Quiz", callback_data="continue_quiz"),
            InlineKeyboardButton(text="Choose New Category", callback_data="choose_new_category"),
            InlineKeyboardButton(text="End Session", callback_data="end_session"),
        ]
    ]
    await query.message.answer("What would you like to do next?", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

    data = await state.get_data()
    if data.get("quiz_in_progress", False):
        await ask_question(query, state)

@quiz_router.callback_query(F.data.startswith("answer_"))
async def handle_answer(query: CallbackQuery, state: FSMContext):
    try:
        selected_answer_index = int(query.data.split("_")[-1])
        data = await state.get_data()
        correct_answer_shuffled_index = data["correct_answer_shuffled_index"]
        
        if selected_answer_index == correct_answer_shuffled_index:
            await state.update_data(score=data["score"] + 1)
            feedback = "✅ Correct!"
        else:
            correct_option = data["shuffled_questions"][data["current_question_index"]]["options"][correct_answer_shuffled_index]
            feedback = f"❌ Incorrect! The correct answer was: {correct_option}"

        await query.message.delete()
        await state.update_data(current_question_index=data["current_question_index"] + 1)
        await query.message.answer(feedback)
        await ask_question(query, state)
    except Exception as e:
        await query.message.answer("There was an issue handling your answer. Please contact support.")
        logging.error(f"Error in handle_answer: {e}")

@quiz_router.callback_query(F.data == "cancel")
async def handle_cancel(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.answer("Quiz session cancelled.")

@quiz_router.callback_query(F.data.startswith("choose_category_"))
async def handle_quiz_selection(query: CallbackQuery, state: FSMContext):
    try:
        category_index = int(query.data.split("_")[-1])
        await state.update_data(category_index=category_index, quiz_name=quiz_data["categories"][category_index]["name"], quiz_in_progress=True)

        await query.message.answer(f"Selected category: {quiz_data['categories'][category_index]['name']}")
        await ask_question(query, state)
    except Exception as e:
        await query.message.answer("There was an issue selecting the quiz category. Please contact support.")
        logging.error(f"Error in handle_quiz_selection: {e}")

@quiz_router.callback_query(F.data == "play_again")
async def handle_play_again(query: CallbackQuery, state: FSMContext):
    try:
        await state.update_data(current_question_index=0, score=0, quiz_in_progress=True)
        await ask_question(query, state)
    except Exception as e:
        await query.message.answer("There was an issue restarting the quiz. Please contact support.")
        logging.error(f"Error in handle_play_again: {e}")

@quiz_router.callback_query(F.data == "choose_another_quiz")
async def handle_choose_another_quiz(query: CallbackQuery, state: FSMContext):
    try:
        await state.clear()
        await show_other_categories_keyboard(query, state)
    except Exception as e:
        await query.message.answer("There was an issue starting a new quiz selection. Please contact support.")
        logging.error(f"Error in handle_choose_another_quiz: {e}")

async def ask_question(query: CallbackQuery, state: FSMContext):
    global quiz_data

    try:
        data = await state.get_data()
        category = quiz_data["categories"][data["category_index"]]
        
        if "shuffled_questions" not in data:
            shuffled_questions = category["questions"][:]
            random.shuffle(shuffled_questions)
            await state.update_data(shuffled_questions=shuffled_questions, current_question_index=0, score=0)
            data = await state.get_data()
        
        questions = data["shuffled_questions"]
        current_index = data["current_question_index"]

        if current_index >= len(questions):
            await end_quiz(query, state)
            return

        question = questions[current_index]
        options = question.get("options", [])

        option_indices = list(range(len(options)))
        random.shuffle(option_indices)
        shuffled_options = [options[i] for i in option_indices]
        correct_answer_shuffled_index = option_indices.index(question["correct_answer_index"])
        await state.update_data(correct_answer_shuffled_index=correct_answer_shuffled_index)

        keyboard = [[InlineKeyboardButton(text=opt, callback_data=f"answer_{i}")] for i, opt in enumerate(shuffled_options)]
        keyboard.append([InlineKeyboardButton(text="❌Cancel❌", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        logging.info(f"Question: {question['question']} with shuffled options: {shuffled_options}")
        await query.message.answer(f"Question {current_index + 1}: {question['question']}", reply_markup=reply_markup)
        await state.update_data(start_time=datetime.now().isoformat())
    except Exception as e:
        await query.message.answer("There was an issue loading the question. Please contact support.")
        logging.error(f"Error in ask_question: {e}")

async def end_quiz(query: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        score = data["score"]
        total_questions = len(quiz_data["categories"][data["category_index"]]["questions"])

        chat_id = query.message.chat.id
        quiz_name = data.get("quiz_name", data.get("category_index"))
        start_time = datetime.fromisoformat(data.get("start_time"))
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        current_question_index = data.get("current_question_index", 0)

        quiz_session_to_save = QuizSession(chat_id, quiz_name, start_time, end_time, score, duration, current_question_index)
        save_session_to_user(quiz_session_to_save)

        await query.message.answer(f"Quiz finished! Your score: {score}/{total_questions}")

        # Correctly show the end game keyboard after the quiz ends
        await show_end_game_keyboard(query, state)
    except Exception as e:
        await query.message.answer("There was an issue ending the quiz. Please contact support.")
        logging.error(f"Error in end_quiz: {e}")

async def show_end_game_keyboard(query: types.CallbackQuery, state: FSMContext):
    """Show end game options: play again or choose another quiz."""
    try:
        keyboard = [
            [InlineKeyboardButton(text="Play Again", callback_data="play_again")],
            [InlineKeyboardButton(text="Choose Another Quiz", callback_data="choose_another_quiz")],
            [InlineKeyboardButton(text="End Session", callback_data="end_session")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await query.message.answer("End of the game! What would you like to do next?", reply_markup=reply_markup)
    except Exception as e:
        await query.message.answer("There was an issue showing the end game options. Please contact support.")
        logging.error(f"Error in show_end_game_keyboard: {e}")