import logging
from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.db_utils import User, add_user_to_db, is_user_in_db
from handlers.quiz_keyboards import show_start_game_keyboard

# Privacy agreement link (can be replaced with actual URL)
PRIVACY_AGREEMENT_LINK = "https://example.com/privacy"

start_router = Router()

@start_router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    """Ask the user for privacy agreement or welcome back if they are in the database."""
    chat_id = message.chat.id
    logging.info(f"Start function: Checking if user {chat_id} exists in the database.")
    
    if is_user_in_db(chat_id):
        await message.answer("Welcome back! Let's start the game!")
        await show_start_game_keyboard(message, state)
    else:
        keyboard = [
            [
                InlineKeyboardButton(text="Yes, I agree", callback_data="accept"),
                InlineKeyboardButton(text="No, I decline", callback_data="decline"),
            ],
            [InlineKeyboardButton(text="End Session", callback_data="end_session")],
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await message.answer(
            f"Welcome! Please review our Privacy Policy and Data Sharing Terms before proceeding: {PRIVACY_AGREEMENT_LINK}\nDo you agree to the terms?",
            reply_markup=reply_markup,
        )

@start_router.callback_query(F.data == "accept")
async def accept_privacy(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text("Thank you for accepting! Please provide your Name:")
    await state.update_data(awaiting_name=True)

@start_router.callback_query(F.data == "decline")
async def decline_privacy(query: CallbackQuery):
    await query.message.edit_text("You must agree to the terms to proceed. Session will end.")
    await query.message.answer("Goodbye!")

@start_router.callback_query(F.data == "end_session")
async def end_session(query: CallbackQuery):
    await query.message.edit_text("Session ended. Goodbye!")

@start_router.message(lambda message: True)
async def collect_name(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get('awaiting_name'):
        user_info = message.text.strip()
        await state.update_data(name=user_info, awaiting_name=False, awaiting_job=True)
        await message.answer("Great! Now, please provide your Job:")
    elif data.get('awaiting_job'):
        user_info = message.text.strip()
        await state.update_data(job=user_info, awaiting_job=False, awaiting_phone_number=True)
        await message.answer("Thank you! Now, please provide your Phone Number:")
    elif data.get('awaiting_phone_number'):
        user_info = message.text.strip()
        await state.update_data(phone_number=user_info, awaiting_phone_number=False, awaiting_email=True)
        await message.answer("Thank you! Finally, please provide your Email:")
    elif data.get('awaiting_email'):
        user_info = message.text.strip()
        data = await state.get_data()
        await state.update_data(email=user_info, awaiting_email=False)

        # Create a User object to store in the database
        user = User(
            chat_id=message.chat.id,
            name=data['name'],
            job=data['job'],
            phone_number=data['phone_number'],
            email=user_info,
            privacy_accepted=1
        )

        # Save the user data to the database
        add_user_to_db(user)

        # Clean up user data from state
        await state.clear()

        await message.answer(f"Thank you for providing all information. Registration complete!")

        # Show the start game keyboard
        await show_start_game_keyboard(message, state)