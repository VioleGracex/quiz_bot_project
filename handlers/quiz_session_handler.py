import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes


# keyboards 

async def show_start_game_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the start game options to play a quiz or end the session."""
    try:
        keyboard = [
            [
                InlineKeyboardButton("Play a Quiz", callback_data="play_quiz"),
                InlineKeyboardButton("End Session", callback_data="end_session"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Welcome to the quiz! Choose an option:", reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text("There was an issue showing the start game options. Please contact support.")
        logging.error(f"Error in show_start_game_keyboard: {e}")

async def show_end_game_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the end game options to play again or choose another quiz."""
    try:
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data="play_again"),  # Change from play_quiz to play_again
                InlineKeyboardButton("Choose Another Quiz", callback_data="choose_another_quiz"),
                InlineKeyboardButton("End Session", callback_data="end_session"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("Game Over! What would you like to do next?", reply_markup=reply_markup)

    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue showing the end game options. Please contact support.")
        logging.error(f"Error in show_end_game_keyboard: {e}")

# Load categories and questions from JSON file with error checking
def load_quiz_data():
    try:
        with open('data/quiz_data.json', 'r') as file:
            quiz_data = json.load(file)
        
        # Check if the necessary structure exists in the loaded JSON
        if not isinstance(quiz_data, dict):
            raise ValueError("Quiz data should be a dictionary.")
        
        if "categories" not in quiz_data:
            raise KeyError("'categories' key is missing in the quiz data.")
        
        # Validate each category
        for category in quiz_data["categories"]:
            if "name" not in category or "questions" not in category:
                raise KeyError(f"Missing 'name' or 'questions' in category {category}.")
            # Validate each question in the category
            for question in category["questions"]:
                if "question" not in question or "correct_answer_index" not in question:
                    raise KeyError(f"Missing 'question' or 'correct_answer_index' in question {question}.")
                if "options" not in question:
                    raise KeyError(f"Missing 'options' in question {question}.")
        
        return quiz_data

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logging.error(f"Error loading quiz data: {e}")
        raise Exception("Answers were not loaded correctly. Please contact support.")  # Raise an exception for the error

# Initialize the quiz session handler
async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main quiz menu with options to start a quiz or end the session."""
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

async def quiz_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses for quiz actions and navigating through questions."""
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "end_session":
            await query.edit_message_text("Thanks for playing! We hope you enjoyed the quiz. Check out our other products!")
            context.user_data.clear()
            return

        elif query.data == "play_quiz":
            # Show categories to choose from
            quiz_data = load_quiz_data()
            keyboard = [
                [InlineKeyboardButton(f"{category['name']} - {len(category['questions'])} questions", callback_data=f"choose_category_{i}")]
                for i, category in enumerate(quiz_data["categories"])
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Please choose a category to start the quiz:", reply_markup=reply_markup)
            context.user_data['quiz_in_progress'] = True

        elif query.data.startswith("choose_category_"):
            # Get the category index and start the quiz
            category_index = int(query.data.split("_")[-1])
            quiz_data = load_quiz_data()
            category = quiz_data["categories"][category_index]
            
            # Save the category index in user data
            context.user_data['category_index'] = category_index
            context.user_data['current_question_index'] = 0
            context.user_data['score'] = 0
            
            # Start the quiz with the first question
            await query.edit_message_text(f"Starting quiz in the '{category['name']}' category. Good luck!")
            await ask_question(update, context)

        elif query.data == "play_again":
            # Get the last category played from user data and restart the quiz
            category_index = context.user_data.get('category_index')
            if category_index is not None:
                quiz_data = load_quiz_data()
                category = quiz_data["categories"][category_index]
                
                # Reset score and question index, and start the quiz again
                context.user_data['current_question_index'] = 0
                context.user_data['score'] = 0
                await query.edit_message_text(f"Starting quiz again in the '{category['name']}' category. Good luck!")
                await ask_question(update, context)
            else:
                await query.edit_message_text("No category found. Please choose a category to start the quiz.")

    except Exception as e:
        await query.edit_message_text("There was an issue during the quiz. Please contact support.")
        logging.error(f"Error in quiz_button: {e}")


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the current question and handle the user's response."""
    try:
        quiz_data = load_quiz_data()
        category = quiz_data["categories"][context.user_data['category_index']]
        questions = category['questions']
        
        current_index = context.user_data['current_question_index']
        
        # Check if we've run out of questions
        if current_index >= len(questions):
            await end_quiz(update, context)
            return

        question = questions[current_index]
        options = question.get("options", [])
        keyboard = [[InlineKeyboardButton(opt, callback_data=f"answer_{i}")] for i, opt in enumerate(options)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        logging.info(f"Question: {question['question']} with options: {options}")
        await update.callback_query.message.reply_text(f"Question {current_index + 1}: {question['question']}", reply_markup=reply_markup)

    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue loading the question. Please contact support.")
        logging.error(f"Error in ask_question: {e}")

async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End the quiz, show the user's final score, and provide options to play again or end the session."""
    try:
        score = context.user_data['score']
        total_questions = len(load_quiz_data()['categories'][context.user_data['category_index']]['questions'])

        # Show the final score
        await update.callback_query.message.reply_text(f"Quiz finished! Your score: {score}/{total_questions}")

        # Show the end game options (e.g., play again or end session)
        await show_end_game_keyboard(update, context)

    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue ending the quiz. Please contact support.")
        logging.error(f"Error in end_quiz: {e}")

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the answer selection and updates the score."""
    try:
        query = update.callback_query
        await query.answer()
        
        # Get the question and answer indices
        category_index = context.user_data['category_index']
        quiz_data = load_quiz_data()
        category = quiz_data["categories"][category_index]
        questions = category['questions']
        current_index = context.user_data['current_question_index']
        
        # Check if the answer is correct
        question = questions[current_index]
        selected_answer_index = int(query.data.split("_")[-1])
        correct_answer_index = question['correct_answer_index']
        
        if selected_answer_index == correct_answer_index:
            context.user_data['score'] += 1
        
        # Move to the next question
        context.user_data['current_question_index'] += 1
        await ask_question(update, context)

    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue handling your answer. Please contact support.")
        logging.error(f"Error in handle_answer: {e}")


# Update handle_end_game_action to restart from the last category played
async def handle_end_game_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the end game action based on user choice."""
    try:
        query = update.callback_query
        await query.answer()

        if query.data == "play_again":
            # Get the last category played and restart the quiz
            category_index = context.user_data.get('category_index', None)
            if category_index is None:
                await query.edit_message_text("No category was selected. Please choose a quiz to play.")
                return
            
            # Reset the question index and score
            context.user_data['current_question_index'] = 0
            context.user_data['score'] = 0
            quiz_data = load_quiz_data()
            category = quiz_data["categories"][category_index]
            await query.edit_message_text(f"Starting quiz again in the '{category['name']}' category. Good luck!")
            await ask_question(update, context)  # Start the quiz from the first question of the same category

        elif query.data == "choose_another_quiz":
            # Show categories again to start a new quiz
            quiz_data = load_quiz_data()
            keyboard = [
                [InlineKeyboardButton(f"{category['name']} - {len(category['questions'])} questions", callback_data=f"choose_category_{i}")]
                for i, category in enumerate(quiz_data["categories"])
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Please choose a category to start a new quiz:", reply_markup=reply_markup)
            context.user_data['quiz_in_progress'] = True

        elif query.data == "end_session":
            # End the session
            await query.edit_message_text("Thanks for playing! We hope you enjoyed the quiz. Check out our other products!")
            context.user_data.clear()

    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue processing your request. Please contact support.")
        logging.error(f"Error in handle_end_game_action: {e}")
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel the registration and clear user data."""
    if update.message.text.strip().lower() == "cancel":
        await update.message.reply_text("Quiz session cancelled.")
        context.user_data.clear()

def setup_session_handlers(application: Application) -> None:
    """Sets up all the handlers for the quiz bot."""
    # Handlers
    application.add_handler(CommandHandler("quiz_start", quiz_start))
    application.add_handler(CallbackQueryHandler(quiz_button, pattern="^(play_quiz|end_session|choose_category_\\d+|play_again)$"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_\\d+$"))
    application.add_handler(CallbackQueryHandler(handle_end_game_action, pattern="^(play_quiz|choose_another_quiz|end_session)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cancel))
