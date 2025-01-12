from telegram import Update
from telegram.ext import CallbackContext
from utils.db_utils import register_user

async def start(update: Update, context: CallbackContext):
    user_data = {"chat_id": update.effective_chat.id}
    await update.message.reply_text("Welcome! Let's register. Please enter your name:")

    def collect_data():
        context.user_data["step"] = "collect_name"

    context.user_data.update(user_data)
    collect_data()

async def handle_user_input(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    step = context.user_data.get("step", None)

    if step == "collect_name":
        context.user_data["name"] = update.message.text
        await update.message.reply_text("Enter your email:")
        context.user_data["step"] = "collect_email"

    elif step == "collect_email":
        context.user_data["email"] = update.message.text
        await update.message.reply_text("Enter your job title:")
        context.user_data["step"] = "collect_job"

    elif step == "collect_job":
        context.user_data["job"] = update.message.text
        await update.message.reply_text("Enter your phone number:")
        context.user_data["step"] = "collect_phone"

    elif step == "collect_phone":
        context.user_data["phone"] = update.message.text
        register_user(chat_id, context.user_data)
        await update.message.reply_text("Registration complete! Type /menu to choose a quiz.")
