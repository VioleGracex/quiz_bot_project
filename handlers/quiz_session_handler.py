import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Load categories and questions from JSON file
def load_quiz_data():
    with open('quiz_data.json', 'r') as file:
        return json.load(file)

# Initialize the quiz session handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main quiz menu with options to start a quiz or end the session."""
    keyboard = [
        [
            InlineKeyboardButton("Play a Quiz", callback_data="play_quiz"),
            InlineKeyboardButton("End Session", callback_data="end_session"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to the quiz! Choose an option:", reply_markup=reply_markup)

    context.user_data['quiz_in_progress'] = False
    context.user_data['score'] = 0
    context.user_data['current_question_index'] = 0

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses for quiz actions and navigating through questions."""
    query = update.callback_query
    await query.answer()

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
        
        # Start the quiz with the first question
        context.user_data['category_index'] = category_index
        context.user_data['current_question_index'] = 0
        context.user_data['score'] = 0
        
        await query.edit_message_text(f"Starting quiz in the '{category['name']}' category. Good luck!")
        await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the current question and handle the user's response."""
    quiz_data = load_quiz_data()
    category = quiz_data["categories"][context.user_data['category_index']]
    questions = category['questions']
    
    current_index = context.user_data['current_question_index']
    if current_index < len(questions):
        question = questions[current_index]
        keyboard = [
            InlineKeyboardButton(answer, callback_data=f"answer_{i}")
            for i, answer in enumerate(question['answers'])
        ]
        reply_markup = InlineKeyboardMarkup([keyboard])
        await update.message.reply_text(f"Question {current_index + 1}: {question['question']}", reply_markup=reply_markup)
    else:
        # End of quiz
        score = context.user_data['score']
        await update.message.reply_text(f"Quiz completed! Your score: {score}/{len(questions)}")
        await show_end_game_keyboard(update, context)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the answer selection and updates the score."""
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

async def show_end_game_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the end game options to play again or choose another quiz."""
    keyboard = [
        [
            InlineKeyboardButton("Play Again", callback_data="play_quiz"),
            InlineKeyboardButton("Choose Another Quiz", callback_data="choose_another_quiz"),
            InlineKeyboardButton("End Session", callback_data="end_session"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Game Over! What would you like to do next?", reply_markup=reply_markup)

async def handle_end_game_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the end game action based on user choice."""
    query = update.callback_query
    await query.answer()

    if query.data == "play_quiz":
        # Start a new quiz
        await query.edit_message_text("Please choose a category to start the quiz:")
        context.user_data['quiz_in_progress'] = False

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

def setup_session_handlers(application: Application) -> None:
    """Sets up all the handlers for the quiz bot."""
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button, pattern="^(play_quiz|end_session|choose_category_\\d+)$"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_\\d+$"))
    application.add_handler(CallbackQueryHandler(handle_end_game_action, pattern="^(play_quiz|choose_another_quiz|end_session)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cancel))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel the registration and clear user data."""
    if update.message.text.strip().lower() == "cancel":
        await update.message.reply_text("Quiz session cancelled.")
        context.user_data.clear()