from email.mime import application
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from handlers.quiz_session_handler import show_start_game_keyboard
from models.user_model import User
from utils.db_utils import add_user_to_db, is_user_in_db


# Privacy agreement link (can be replaced with actual URL)
PRIVACY_AGREEMENT_LINK = "https://example.com/privacy"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the user for privacy agreement or welcome back if they are in the database."""
    chat_id = update.message.chat.id  # Use chat_id instead of user_id
    print(f"Start function: Checking if user {chat_id} exists in the database.")
    
    # Check if the user exists in the database
    if is_user_in_db(chat_id):
        # If the user exists, welcome back and show the start game keyboard
        await update.message.reply_text("Welcome back! Let's start the game!")
        await show_start_game_keyboard(update, context)
        return  # Exit the function early to skip the privacy agreement process
    
    # If the user does not exist, ask for the privacy agreement
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

        # Create a User object to store in the database
        user = User(
            chat_id=update.message.chat.id,  # Use the chat_id as unique identifier
            name=context.user_data['name'],
            job=context.user_data['job'],
            phone_number=context.user_data['phone_number'],
            email=context.user_data['email'],
            privacy_accepted=1  # Set privacy accepted to 1
        )

        # Save the user data to the database
        add_user_to_db(user)

        # Clean up user data from context
        del context.user_data['awaiting_email']
        del context.user_data['name']
        del context.user_data['job']
        del context.user_data['phone_number']
        del context.user_data['email']

        # Show the start game keyboard
        await show_start_game_keyboard(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel the registration and clear user data."""
    if update.message.text.strip().lower() == "cancel":
        await update.message.reply_text("Registration process cancelled.")
        context.user_data.clear()


def setup_start_handlers(application: application) -> None:
    """Sets up all the handlers for the bot."""
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button, pattern="^(accept|decline|end_session)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_user_info))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cancel))  
