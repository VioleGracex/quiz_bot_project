import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers.start_handler import start, handle_user_input
from handlers.menu_handler import show_quiz_menu
from handlers.quiz_handler import start_quiz, end_quiz

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)

# Main function to start the bot
def main():
    # Create the Application instance
    application = Application.builder().token("7530128693:AAFcG6SiN2aU9paJuIvsdIskggQ9aTAW2m8").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
    application.add_handler(CommandHandler("menu", show_quiz_menu))
    application.add_handler(CallbackQueryHandler(start_quiz, pattern="quiz"))
    application.add_handler(CallbackQueryHandler(end_quiz, pattern="^end$"))

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
