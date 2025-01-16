import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import quiz_data

async def show_start_game_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать опции начала игры: начать викторину или завершить сеанс."""
    try:
        if context.user_data.get('quiz_in_progress', False):
            keyboard = [
                [
                    InlineKeyboardButton("Продолжить викторину", callback_data="continue_quiz"),
                    InlineKeyboardButton("Выбрать новую категорию", callback_data="choose_new_category"),
                    InlineKeyboardButton("Завершить сеанс", callback_data="end_session"),
                ]
            ]
            await update.message.reply_text("У вас есть незавершенная викторина. Что вы хотите сделать дальше?", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            # Показать доступные категории викторин
            categories = quiz_data["categories"]
            keyboard = [
                [InlineKeyboardButton(f"{category['name']} - {len(category['questions'])} вопросов", callback_data=f"choose_category_{i}")]
                for i, category in enumerate(categories)
            ]
            await update.message.reply_text("Добро пожаловать в викторину! Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text("Произошла ошибка при показе опций начала игры. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в show_start_game_keyboard: {e}")

async def show_end_game_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать опции завершения игры: играть снова или выбрать другую викторину."""
    try:
        keyboard = [
            [
                InlineKeyboardButton("Играть снова", callback_data="play_again"),
                InlineKeyboardButton("Выбрать другую викторину", callback_data="choose_another_quiz"),
                InlineKeyboardButton("Завершить сеанс", callback_data="end_session"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("Игра окончена! Что вы хотите сделать дальше?", reply_markup=reply_markup)
    except Exception as e:
        await update.callback_query.message.reply_text("Произошла ошибка при показе опций завершения игры. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в show_end_game_keyboard: {e}")

async def show_other_categories_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать клавиатуру с другими категориями викторин."""
    try:
        categories = quiz_data["categories"]
        keyboard = [
            [InlineKeyboardButton(f"{category['name']} - {len(category['questions'])} вопросов", callback_data=f"choose_category_{i}")]
            for i, category in enumerate(categories)
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text("Добро пожаловать в викторину! Выберите категорию:", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text("Добро пожаловать в викторину! Выберите категорию:", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Ошибка в show_other_categories_keyboard: {e}")
        if update.message:
            await update.message.reply_text("Произошла ошибка при показе категорий викторин. Пожалуйста, свяжитесь с поддержкой.")
        elif update.callback_query:
            await update.callback_query.message.reply_text("Произошла ошибка при показе категорий викторин. Пожалуйста, свяжитесь с поддержкой.")