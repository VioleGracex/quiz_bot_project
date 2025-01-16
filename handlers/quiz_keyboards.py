import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import quiz_data
async def show_start_game_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show start game options: start quiz or end session."""
    try:
        if context.user_data.get('quiz_in_progress', False):
            keyboard = [
                [
                    InlineKeyboardButton("Continue Quiz", callback_data="continue_quiz"),
                    InlineKeyboardButton("Choose New Category", callback_data="choose_new_category"),
                    InlineKeyboardButton("End Session", callback_data="end_session"),
                ]
            ]
            await update.message.reply_text("You have an ongoing quiz. What would you like to do next?", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            # Display available quiz categories
            categories = quiz_data["categories"]
            keyboard = [
                [InlineKeyboardButton(f"{category['name']} - {len(category['questions'])} questions", callback_data=f"choose_category_{i}")]
                for i, category in enumerate(categories)
            ]
            await update.message.reply_text("Welcome to the quiz! Choose a category:", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text("There was an issue showing the start game options. Please contact support.")
        logging.error(f"Error in show_start_game_keyboard: {e}")

async def show_end_game_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show end game options: play again or choose another quiz."""
    try:
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data="play_again"),
                InlineKeyboardButton("Choose Another Quiz", callback_data="choose_another_quiz"),
                InlineKeyboardButton("End Session", callback_data="end_session"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("End of the game! What would you like to do next?", reply_markup=reply_markup)
    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue showing the end game options. Please contact support.")
        logging.error(f"Error in show_end_game_keyboard: {e}")


async def show_other_categories_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the keyboard with other quiz categories."""
    try:
        categories = quiz_data["categories"]
        keyboard = [
            [InlineKeyboardButton(f"{category['name']} - {len(category['questions'])} questions", callback_data=f"choose_category_{i}")]
            for i, category in enumerate(categories)
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text("Welcome to the quiz! Choose a category:", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text("Welcome to the quiz! Choose a category:", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in show_other_categories_keyboard: {e}")
        if update.message:
            await update.message.reply_text("There was an issue showing the quiz categories. Please contact support.")
        elif update.callback_query:
            await update.callback_query.message.reply_text("There was an issue showing the quiz categories. Please contact support.")
            await update.message.reply_text("Welcome to the quiz! Choose a category:", reply_markup=InlineKeyboardMarkup(keyboard))