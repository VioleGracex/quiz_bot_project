from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton

async def show_quiz_menu(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("General Knowledge", callback_data="generalknowledge")],
        [InlineKeyboardButton("Science", callback_data="science")],
        [InlineKeyboardButton("History", callback_data="history")],
        [InlineKeyboardButton("Sports", callback_data="sports")],
        [InlineKeyboardButton("End", callback_data="end")]
    ] 

    await update.message.reply_text("Choose a quiz:", reply_markup=InlineKeyboardMarkup(keyboard))
