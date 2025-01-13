import logging
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from models.user_model import User
from utils.db_utils import DB_PATH, create_users_table, add_user_to_db, delete_user_from_db, get_user_by_chat_id


# Logging configuration
logging.basicConfig(level=logging.INFO)

# Privacy Agreement Link (replace with actual URL)
PRIVACY_AGREEMENT_LINK = "https://example.com/privacy"

# Main menu keyboard
def main_menu_keyboard():
    return ReplyKeyboardMarkup([["Play Quiz", "End Session"], ["Delete Account"]], resize_keyboard=True)

# Privacy agreement keyboard (Yes and No options as callback buttons)
def privacy_agreement_keyboard():
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="accept"),
         InlineKeyboardButton("No", callback_data="decline")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Input prompt keyboard with Cancel option
def input_with_cancel_keyboard():
    return ReplyKeyboardMarkup([["Cancel"]], resize_keyboard=True)

# Handlers

# Start handler
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Get the user from the database
    user = get_user_by_chat_id(chat_id)
    
    if user:
        # If user exists, check if they have accepted the privacy terms
        if user.privacy_accepted:
            # User has accepted privacy terms, greet them and show the main menu
            await update.message.reply_text(f"Welcome back, {user.name}!", reply_markup=main_menu_keyboard())
        else:
            # User hasn't accepted privacy terms, prompt them to accept
            await update.message.reply_text(
                f"Welcome! Please review our Privacy Policy and Data Sharing Terms before proceeding: {PRIVACY_AGREEMENT_LINK}\n"
                "Do you agree to the terms? Please choose 'Yes' to accept or 'No' to decline.",
                reply_markup=privacy_agreement_keyboard()
            )
            context.user_data['privacy_accepted'] = False  # Initialize privacy_accepted state
    else:
        # If user doesn't exist, start the registration process
        await update.message.reply_text(
            f"Welcome! Please review our Privacy Policy and Data Sharing Terms before proceeding: {PRIVACY_AGREEMENT_LINK}\n"
            "Do you agree to the terms? Please choose 'Yes' to accept or 'No' to decline.",
            reply_markup=privacy_agreement_keyboard()
        )
        context.user_data['privacy_accepted'] = False  # Initialize privacy_accepted state

# Handle privacy agreement response
async def handle_privacy_agreement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        response = query.data  # 'accept' or 'decline'
        
        if context.user_data.get('awaiting_privacy_confirmation', False):
            if response == "accept":
                await query.answer()  # Acknowledge the response
                await query.edit_message_text("Thank you! Please provide your Name.", reply_markup=input_with_cancel_keyboard())
                context.user_data['name'] = True
                del context.user_data['privacy_accepted']
                
            elif response == "decline":
                await query.answer()  # Acknowledge the response
                await query.edit_message_text("You must agree to the terms to proceed.")
                del context.user_data['privacy_accepted']
            else:
                await query.edit_message_text("Invalid response. Please choose 'Yes' or 'No'.")
                
    elif update.message:
        message = update.message.text.strip().lower()

        if context.user_data.get('awaiting_name', False):
            context.user_data['name'] = message
            await update.message.reply_text("Great! Now, please provide your Job.", reply_markup=input_with_cancel_keyboard())
            context.user_data['awaiting_name'] = False
            context.user_data['awaiting_job'] = True
        
        elif context.user_data.get('awaiting_job', False):
            context.user_data['job'] = message
            # Proceed to phone number input or end
            await update.message.reply_text("Thank you! Now, please provide your Phone Number.", reply_markup=input_with_cancel_keyboard())
            context.user_data['awaiting_job'] = False
            context.user_data['awaiting_phone_number'] = True

        elif context.user_data.get('awaiting_phone_number', False):
            context.user_data['phone_number'] = message
            await update.message.reply_text("Thank you! Finally, please provide your Email.", reply_markup=input_with_cancel_keyboard())
            context.user_data['awaiting_phone_number'] = False
            context.user_data['awaiting_email'] = True

        elif context.user_data.get('awaiting_email', False):
            context.user_data['email'] = message
            # Finalize registration
            await update.message.reply_text(f"Thank you for providing all information. Registration complete!")
            del context.user_data['awaiting_email']
            del context.user_data['name']
            del context.user_data['job']
            del context.user_data['phone_number']
            del context.user_data['email']

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration process cancelled.", reply_markup=main_menu_keyboard())
    # Clear any data if needed
    context.user_data.clear()

# Delete user handler
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user_by_chat_id(chat_id)
    
    if user:
        # Delete user from the database
        delete_user_from_db(chat_id)
        await update.message.reply_text("Your account has been deleted successfully.", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("No user found to delete.")

# End session handler
async def end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user_by_chat_id(chat_id)
    
    if user:
        await update.message.reply_text("Session closed successfully. Your data has been saved.")
        await update.message.reply_text(f"Your session data: {user.name}, {user.job}, {user.phone_number}, {user.email}")
    else:
        await update.message.reply_text("No active session found.")

# Register handlers
def register_handlers(application):
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CallbackQueryHandler(handle_privacy_agreement, pattern="^(accept|decline)$"))  # Handling privacy agreement button presses
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cancel, pattern="^Cancel$"))
    application.add_handler(CommandHandler("delete", delete_user))
    application.add_handler(CallbackQueryHandler(end_session, pattern="^end$"))
