from email.mime import application
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters


from handlers.quiz_keyboards import show_start_game_keyboard
from utils.db_utils import User, add_user_to_db, is_user_in_db

# Ссылка на соглашение о конфиденциальности (можно заменить на фактический URL)
PRIVACY_AGREEMENT_LINK = "https://example.com/privacy"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Спросите пользователя о соглашении о конфиденциальности или поприветствуйте его, если он уже в базе данных."""
    chat_id = update.message.chat.id  # Используйте chat_id вместо user_id
    print(f"Функция start: Проверка, существует ли пользователь {chat_id} в базе данных.")
    
    # Проверьте, существует ли пользователь в базе данных
    if is_user_in_db(chat_id):
        # Если пользователь существует, поприветствуйте его и покажите клавиатуру начала игры
        await update.message.reply_text("С возвращением! Давайте начнем игру!")
        await show_start_game_keyboard(update, context)
        return  # Выйти из функции, чтобы пропустить процесс соглашения о конфиденциальности
    
    # Если пользователь не существует, спросите о соглашении о конфиденциальности
    keyboard = [
        [
            InlineKeyboardButton("Да, я согласен", callback_data="accept"),
            InlineKeyboardButton("Нет, я не согласен", callback_data="decline"),
        ],
        [InlineKeyboardButton("Завершить сеанс", callback_data="end_session")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Добро пожаловать! Пожалуйста, ознакомьтесь с нашей Политикой конфиденциальности и Условиями обмена данными перед продолжением: {PRIVACY_AGREEMENT_LINK}\nВы согласны с условиями?",
        reply_markup=reply_markup,
    )
    context.user_data['awaiting_privacy_confirmation'] = True  # Указать, что мы ждем подтверждения конфиденциальности

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ответ на соглашение о конфиденциальности или завершение сеанса."""
    query = update.callback_query
    await query.answer()

    if query.data == "accept":
        # Соглашение о конфиденциальности принято, перейти к запросу информации о пользователе
        await query.edit_message_text("Спасибо за принятие! Пожалуйста, укажите свое Имя:")
        context.user_data['privacy_accepted'] = True
        context.user_data['awaiting_name'] = True

    elif query.data == "decline":
        # Соглашение о конфиденциальности отклонено, завершить сеанс
        await query.edit_message_text("Вы должны согласиться с условиями, чтобы продолжить. Сеанс будет завершен.")
        await query.message.reply_text("До свидания!")
        context.user_data.clear()  # Очистить данные пользователя
        return  # Завершить процесс

    elif query.data == "end_session":
        # Завершить сеанс, отменить соединение
        await query.edit_message_text("Сеанс завершен. До свидания!")
        context.user_data.clear()  # Очистить данные пользователя
        return

async def collect_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сбор информации о пользователе после принятия условий конфиденциальности."""
    user_info = update.message.text.strip()

    if context.user_data.get('awaiting_name', False):
        if re.match(r'^[А-Яа-яA-Za-z\s]+$', user_info):
            context.user_data['name'] = user_info
            await update.message.reply_text("Отлично! Теперь, пожалуйста, укажите вашу Профессию:")
            context.user_data['awaiting_name'] = False
            context.user_data['awaiting_job'] = True
        else:
            await update.message.reply_text("Пожалуйста, укажите корректное имя.")

    elif context.user_data.get('awaiting_job', False):
        if re.match(r'^[А-Яа-яA-Za-z\s]+$', user_info):
            context.user_data['job'] = user_info
            await update.message.reply_text("Спасибо! Теперь, пожалуйста, укажите ваш Номер телефона:")
            context.user_data['awaiting_job'] = False
            context.user_data['awaiting_phone_number'] = True
        else:
            await update.message.reply_text("Пожалуйста, укажите корректную профессию.")

    elif context.user_data.get('awaiting_phone_number', False):
        if re.match(r'^\+?\d{10,15}$', user_info):
            context.user_data['phone_number'] = user_info
            await update.message.reply_text("Спасибо! Наконец, пожалуйста, укажите ваш Email:")
            context.user_data['awaiting_phone_number'] = False
            context.user_data['awaiting_email'] = True
        else:
            await update.message.reply_text("Пожалуйста, укажите корректный номер телефона.")

    elif context.user_data.get('awaiting_email', False):
        if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', user_info):
            context.user_data['email'] = user_info
            # Завершить регистрацию
            await update.message.reply_text("Спасибо за предоставленную информацию. Регистрация завершена!")

            # Создать объект User для сохранения в базе данных
            user = User(
                chat_id=update.message.chat.id,  # Используйте chat_id в качестве уникального идентификатора
                name=context.user_data['name'],
                job=context.user_data['job'],
                phone_number=context.user_data['phone_number'],
                email=context.user_data['email'],
                privacy_accepted=1  # Принятие конфиденциальности установлено в 1
            )

            # Сохранить данные пользователя в базе данных
            add_user_to_db(user)

            # Очистить данные пользователя из контекста
            del context.user_data['awaiting_email']
            del context.user_data['name']
            del context.user_data['job']
            del context.user_data['phone_number']
            del context.user_data['email']
            del context.user_data['privacy_accepted'] 

            # Показать клавиатуру начала игры
            await show_start_game_keyboard(update, context)
        else:
            await update.message.reply_text("Пожалуйста, укажите корректный email.")

def setup_start_handlers(application: application) -> None:
    """Настраивает все обработчики для бота."""
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button, pattern="^(accept|decline|end_session)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_user_info))