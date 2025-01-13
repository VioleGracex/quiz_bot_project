import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Privacy agreement link (can be replaced with actual URL)
PRIVACY_AGREEMENT_LINK = "https://example.com/privacy"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the user for privacy agreement."""
    keyboard = [
        [
            InlineKeyboardButton("Yes, I agree", callback_data="accept"),
            InlineKeyboardButton("No, I decline", callback_data="decline"),
        ],
        [InlineKeyboardButton("End Session", callback_data="end_session")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Welcome! Please review our Privacy Policy and Data Sharing Terms before proceeding: {PRIVACY_AGREEMENT_LINK}\nDo you agree to the terms?",
        reply_markup=reply_markup,
    )
    context.user_data['awaiting_privacy_confirmation'] = True  # Indicate that we are waiting for the privacy agreement


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the privacy agreement response or session termination."""
    query = update.callback_query
    await query.answer()

    if query.data == "accept":
        # Privacy accepted, proceed to ask for user info
        await query.edit_message_text("Thank you for accepting! Please provide your Name:")
        context.user_data['privacy_accepted'] = True
        context.user_data['awaiting_name'] = True

    elif query.data == "decline":
        # Privacy declined, end the session
        await query.edit_message_text("You must agree to the terms to proceed. Session will end.")
        await query.message.reply_text("Goodbye!")
        context.user_data.clear()  # Clear user data
        return  # End the process

    elif query.data == "end_session":
        # End session, cancel the connection
        await query.edit_message_text("Session ended. Goodbye!")
        context.user_data.clear()  # Clear user data
        return


async def collect_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Collects user information after accepting privacy terms."""
    user_info = update.message.text.strip()

    if context.user_data.get('awaiting_name', False):
        context.user_data['name'] = user_info
        await update.message.reply_text("Great! Now, please provide your Job:")
        context.user_data['awaiting_name'] = False
        context.user_data['awaiting_job'] = True

    elif context.user_data.get('awaiting_job', False):
        context.user_data['job'] = user_info
        await update.message.reply_text("Thank you! Now, please provide your Phone Number:")
        context.user_data['awaiting_job'] = False
        context.user_data['awaiting_phone_number'] = True

    elif context.user_data.get('awaiting_phone_number', False):
        context.user_data['phone_number'] = user_info
        await update.message.reply_text("Thank you! Finally, please provide your Email:")
        context.user_data['awaiting_phone_number'] = False
        context.user_data['awaiting_email'] = True

    elif context.user_data.get('awaiting_email', False):
        context.user_data['email'] = user_info
        # Finalize registration
        await update.message.reply_text(f"Thank you for providing all information. Registration complete!")
        del context.user_data['awaiting_email']
        del context.user_data['name']
        del context.user_data['job']
        del context.user_data['phone_number']
        del context.user_data['email']


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel the registration and clear user data."""
    if update.message.text.strip().lower() == "cancel":
        await update.message.reply_text("Registration process cancelled.")
        context.user_data.clear()


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7530128693:AAFcG6SiN2aU9paJuIvsdIskggQ9aTAW2m8").build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button, pattern="^(accept|decline|end_session)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_user_info))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cancel))  # Remove 'pattern' argument

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
