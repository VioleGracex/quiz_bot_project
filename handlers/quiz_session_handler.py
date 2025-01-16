from datetime import datetime
import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from email.mime import application
from telegram.ext import   ContextTypes, CommandHandler, CallbackQueryHandler, filters
from handlers.json_functions import load_quiz_data
from handlers.quiz_keyboards import show_other_categories_keyboard, show_start_game_keyboard, show_end_game_keyboard
from config import quiz_data
from utils.db_utils import QuizSession, save_session_to_user



# Initialize a global variable to store quiz data
if quiz_data is None:
    load_quiz_data()

def shuffle_loaded_json():
    global quiz_data
    if quiz_data is None:
        quiz_data = load_quiz_data()  # Load quiz data from your JSON function
        
    for category in quiz_data['categories']:
        random.shuffle(category['questions'])

async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main quiz menu with options to start a quiz or end the session."""
    if quiz_data is None:
        shuffle_loaded_json()
        
    try:
        # Show the start game options
        await show_start_game_keyboard(update, context)

        # Initialize user data for the quiz session
        context.user_data['quiz_in_progress'] = False
        context.user_data['score'] = 0
        context.user_data['current_question_index'] = 0

    except Exception as e:
        await update.message.reply_text("There was an issue starting the quiz. Please contact support.")
        logging.error(f"Error in quiz_start: {e}")

async def continue_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /continue command to remove the old keyboard and show a new one."""
    query = update.message
    try:
        # Remove old keyboard
        await query.reply_text(
            "Continuing your quiz session...",
            reply_markup=InlineKeyboardMarkup([[]])
        )
        
        # Show new keyboard options
        keyboard = [
            [
                InlineKeyboardButton("Continue Quiz", callback_data="continue_quiz"),
                InlineKeyboardButton("Choose New Category", callback_data="choose_new_category"),
                InlineKeyboardButton("End Session", callback_data="end_session"),
            ]
        ]
        await query.reply_text("What would you like to do next?", reply_markup=InlineKeyboardMarkup(keyboard))

        # If there's an ongoing quiz, ask the next question
        if context.user_data.get('quiz_in_progress', False):
            await ask_question(update, context)

    except Exception as e:
        await query.reply_text("There was an issue continuing the quiz. Please contact support.")
        logging.error(f"Error in continue_quiz: {e}")

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the current question, randomize question and answer order, and handle the user's response."""
    global quiz_data

    try:
        category = quiz_data["categories"][context.user_data['category_index']]
        
        # Shuffle questions on the first access
        if 'shuffled_questions' not in context.user_data:
            shuffled_questions = category['questions'][:]
            random.shuffle(shuffled_questions)
            context.user_data['shuffled_questions'] = shuffled_questions
            context.user_data['current_question_index'] = 0
            context.user_data['score'] = 0  # Initialize score
        
        questions = context.user_data['shuffled_questions']
        current_index = context.user_data['current_question_index']

        # Check if we've run out of questions
        if current_index >= len(questions):
            await end_quiz(update, context)
            return

        question = questions[current_index]
        options = question.get("options", [])

        # Shuffle the order of options and store correct answer index
        option_indices = list(range(len(options)))
        random.shuffle(option_indices)
        shuffled_options = [options[i] for i in option_indices]
        correct_answer_shuffled_index = option_indices.index(question['correct_answer_index'])
        context.user_data['correct_answer_shuffled_index'] = correct_answer_shuffled_index  # Track for correctness check

        keyboard = [[InlineKeyboardButton(opt, callback_data=f"answer_{i}")] for i, opt in enumerate(shuffled_options)]
        # Add a cancel button
        keyboard.append([InlineKeyboardButton("❌Cancel❌", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        logging.info(f"Question: {question['question']} with shuffled options: {shuffled_options}")
        await update.callback_query.message.reply_text(
            f"Question {current_index + 1}: {question['question']}",
            reply_markup=reply_markup
        )
        context.user_data['start_time'] = datetime.now().isoformat()
    
    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue loading the question. Please contact support.")
        logging.error(f"Error in ask_question: {e}")

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the answer selection and updates the score."""
    try:
        query = update.callback_query
        await query.answer()
        
        # Retrieve the correct shuffled index for the answer
        selected_answer_index = int(query.data.split("_")[-1])
        correct_answer_shuffled_index = context.user_data['correct_answer_shuffled_index']
        
        # Provide feedback on the selected answer
        if selected_answer_index == correct_answer_shuffled_index:
            context.user_data['score'] += 1
            feedback = "✅ Correct!"
        else:
            correct_option = context.user_data['shuffled_questions'][context.user_data['current_question_index']]['options'][correct_answer_shuffled_index]
            feedback = f"❌ Incorrect! The correct answer was: {correct_option}"

        # Delete the old question message
        await query.message.delete()

        # Move to the next question
        context.user_data['current_question_index'] += 1

        # Show feedback and next question
        await query.message.reply_text(feedback)
        await ask_question(update, context)

    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue handling your answer. Please contact support.")
        logging.error(f"Error in handle_answer: {e}")

async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the cancel button press."""
    query = update.callback_query
    await query.answer()

    # Clear the quiz data from user context
    context.user_data.clear()
    
    await query.message.reply_text("Quiz session cancelled.")
async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End the quiz, show the user's final score, save the session, and provide options to play again or end the session."""
    try:
        score = context.user_data['score']
        total_questions = len(quiz_data['categories'][context.user_data['category_index']]['questions'])

        # Save the session data
        chat_id = update.effective_chat.id
        quiz_name = context.user_data.get('quiz_name', context.user_data.get('category_index'))
        start_time = datetime.fromisoformat(context.user_data.get('start_time'))
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        current_question_index = context.user_data.get('current_question_index', 0)

        # Create and save the QuizSession
        quiz_session_to_save = QuizSession(chat_id, quiz_name, start_time, end_time, score, duration, current_question_index)
        save_session_to_user(quiz_session_to_save)

        # Show the final score
        await update.callback_query.message.reply_text(f"Quiz finished! Your score: {score}/{total_questions}")

        # Show the end game options (e.g., play again or end session)
        await show_end_game_keyboard(update, context)

    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue ending the quiz. Please contact support.")
        logging.error(f"Error in end_quiz: {e}")
async def handle_quiz_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quiz category selection."""
    query = update.callback_query
    await query.answer()
    
    try:
        category_index = int(query.data.split("_")[-1])
        context.user_data['category_index'] = category_index
        context.user_data['quiz_name'] = quiz_data['categories'][category_index]['name']
        context.user_data['quiz_in_progress'] = True

        await query.message.reply_text(f"Selected category: {quiz_data['categories'][category_index]['name']}")
        await ask_question(update, context)
    
    except Exception as e:
        await query.message.reply_text("There was an issue selecting the quiz category. Please contact support.")
        logging.error(f"Error in handle_quiz_selection: {e}")

async def handle_play_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the play again button to restart the quiz."""
    query = update.callback_query
    await query.answer()

    try:
        # Reset user data for the quiz session
        context.user_data['current_question_index'] = 0
        context.user_data['score'] = 0
        context.user_data['quiz_in_progress'] = True
        
        await ask_question(update, context)
    
    except Exception as e:
        await query.message.reply_text("There was an issue restarting the quiz. Please contact support.")
        logging.error(f"Error in handle_play_again: {e}")

async def handle_choose_another_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the choose another quiz button to start a new quiz selection."""
    query = update.callback_query
    await query.answer()

    try:
        # Clear previous quiz data
        context.user_data.clear()
        
        # Show start game options to choose a new quiz category
        await show_other_categories_keyboard(update, context)
    
    except Exception as e:
        if query.message:
            await query.message.reply_text("There was an issue starting a new quiz selection. Please contact support.")
        logging.error(f"Error in handle_choose_another_quiz: {e}")

async def quiz_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses for quiz actions and navigating through questions."""
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "choose_another_quiz":
            # Show categories again to start a new quiz
            await show_start_game_keyboard(update, context)
            context.user_data['quiz_in_progress'] = True

    except Exception as e:
        await query.edit_message_text("There was an issue during the quiz. Please contact support.")
        logging.error(f"Error in quiz_button: {e}")


def setup_session_handlers(application: application) -> None:
    application.add_handler(CommandHandler("quiz_start", quiz_start))
    application.add_handler(CommandHandler("continue", continue_quiz))
    application.add_handler(CallbackQueryHandler(handle_quiz_selection, pattern="^choose_category_\\d+$"))
    application.add_handler(CallbackQueryHandler(ask_question, pattern="^play_quiz$"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_\\d+$"))
    application.add_handler(CallbackQueryHandler(handle_cancel, pattern="^cancel$"))
    application.add_handler(CallbackQueryHandler(handle_play_again, pattern="^play_again$"))
    application.add_handler(CallbackQueryHandler(handle_choose_another_quiz, pattern="^choose_another_quiz"))
    application.add_handler(CallbackQueryHandler(quiz_button, pattern="^(play_quiz|end_session|choose_category_\\d+|play_again|continue_quiz)"))