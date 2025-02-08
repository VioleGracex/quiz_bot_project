import logging
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from config import quiz_data

async def show_start_game_keyboard(message: types.Message, state: FSMContext):
    """Show start game options: start quiz or end session."""
    try:
        data = await state.get_data()
        if data.get('quiz_in_progress', False):
            keyboard = [
                [InlineKeyboardButton(text="Continue Quiz", callback_data="continue_quiz")],
                [InlineKeyboardButton(text="Choose New Category", callback_data="choose_new_category")],
                [InlineKeyboardButton(text="End Session", callback_data="end_session")]
            ]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await message.reply("You have an ongoing quiz. What would you like to do next?", reply_markup=reply_markup)
        else:
            # Display available quiz categories
            categories = quiz_data["categories"]
            keyboard = [
                [InlineKeyboardButton(text=f"{category['name']} - {len(category['questions'])} questions", callback_data=f"choose_category_{i}")]
                for i, category in enumerate(categories)
            ]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await message.reply("Welcome to the quiz! Choose a category:", reply_markup=reply_markup)
    except Exception as e:
        await message.reply("There was an issue showing the start game options. Please contact support.")
        logging.error(f"Error in show_start_game_keyboard: {e}")
        
async def show_end_game_keyboard(query: types.CallbackQuery, state: FSMContext):
    """Show end game options: play again or choose another quiz."""
    try:
        keyboard = [
            [InlineKeyboardButton(text="Play Again", callback_data="play_again")],
            [InlineKeyboardButton(text="Choose Another Quiz", callback_data="choose_another_quiz")],
            [InlineKeyboardButton(text="End Session", callback_data="end_session")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await query.message.reply("End of the game! What would you like to do next?", reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply("There was an issue showing the end game options. Please contact support.")
        logging.error(f"Error in show_end_game_keyboard: {e}")

async def show_other_categories_keyboard(query: types.CallbackQuery, state: FSMContext):
    """Show the keyboard with other quiz categories."""
    try:
        categories = quiz_data["categories"]
        keyboard = [
            [InlineKeyboardButton(text=f"{category['name']} - {len(category['questions'])} questions", callback_data=f"choose_category_{i}")]
            for i, category in enumerate(categories)
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        if query.message:
            await query.message.reply("Welcome to the quiz! Choose a category:", reply_markup=reply_markup)
        elif query.callback_query:
            await query.callback_query.message.reply("Welcome to the quiz! Choose a category:", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in show_other_categories_keyboard: {e}")
        if query.message:
            await query.message.reply("There was an issue showing the quiz categories. Please contact support.")
        elif query.callback_query:
            await query.callback_query.message.reply("There was an issue showing the quiz categories. Please contact support.")