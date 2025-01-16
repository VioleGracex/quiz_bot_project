from datetime import datetime
import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from email.mime import application
from handlers.json_functions import load_quiz_data
from handlers.quiz_keyboards import show_other_categories_keyboard, show_start_game_keyboard, show_end_game_keyboard
from config import quiz_data
from utils.db_utils import QuizSession, save_session_to_user

# Инициализация глобальной переменной для хранения данных викторины
if quiz_data is None:
    load_quiz_data()

def shuffle_loaded_json():
    global quiz_data
    if quiz_data is None:
        quiz_data = load_quiz_data()  # Загрузка данных викторины из JSON
        
    for category in quiz_data['categories']:
        random.shuffle(category['questions'])

async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать главное меню викторины с опциями начать викторину или завершить сеанс."""
    if quiz_data is None:
        shuffle_loaded_json()
        
    try:
        # Показать опции начала игры
        await show_start_game_keyboard(update, context)

        # Инициализация пользовательских данных для сеанса викторины
        context.user_data['quiz_in_progress'] = False
        context.user_data['score'] = 0
        context.user_data['current_question_index'] = 0

    except Exception as e:
        await update.message.reply_text("Произошла ошибка при запуске викторины. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в quiz_start: {e}")

async def continue_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /continue для удаления старой клавиатуры и показа новой."""
    query = update.message
    try:
        # Удалить старую клавиатуру
        await query.reply_text(
            "Продолжение сеанса викторины...",
            reply_markup=InlineKeyboardMarkup([[]])
        )
        
        # Показать новые опции клавиатуры
        keyboard = [
            [
                InlineKeyboardButton("Продолжить викторину", callback_data="continue_quiz"),
                InlineKeyboardButton("Выбрать новую категорию", callback_data="choose_new_category"),
                InlineKeyboardButton("Завершить сеанс", callback_data="end_session"),
            ]
        ]
        await query.reply_text("Что вы хотите сделать дальше?", reply_markup=InlineKeyboardMarkup(keyboard))

        # Если идет викторина, задать следующий вопрос
        if context.user_data.get('quiz_in_progress', False):
            await ask_question(update, context)

    except Exception as e:
        await query.reply_text("Произошла ошибка при продолжении викторины. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в continue_quiz: {e}")

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Задать текущий вопрос, случайным образом перемешать порядок вопросов и ответов и обработать ответ пользователя."""
    global quiz_data

    try:
        category = quiz_data["categories"][context.user_data['category_index']]
        
        # Перемешать вопросы при первом доступе
        if 'shuffled_questions' not in context.user_data:
            shuffled_questions = category['questions'][:]
            random.shuffle(shuffled_questions)
            context.user_data['shuffled_questions'] = shuffled_questions
            context.user_data['current_question_index'] = 0
            context.user_data['score'] = 0  # Инициализация счета
        
        questions = context.user_data['shuffled_questions']
        current_index = context.user_data['current_question_index']

        # Проверить, закончились ли вопросы
        if current_index >= len(questions):
            await end_quiz(update, context)
            return

        question = questions[current_index]
        options = question.get("options", [])

        # Перемешать порядок опций и сохранить индекс правильного ответа
        option_indices = list(range(len(options)))
        random.shuffle(option_indices)
        shuffled_options = [options[i] for i in option_indices]
        correct_answer_shuffled_index = option_indices.index(question['correct_answer_index'])
        context.user_data['correct_answer_shuffled_index'] = correct_answer_shuffled_index  # Отслеживание для проверки правильности

        keyboard = [[InlineKeyboardButton(opt, callback_data=f"answer_{i}")] for i, opt in enumerate(shuffled_options)]
        # Добавить кнопку отмены
        keyboard.append([InlineKeyboardButton("❌Отмена❌", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        logging.info(f"Вопрос: {question['question']} с перемешанными опциями: {shuffled_options}")
        await update.callback_query.message.reply_text(
            f"Вопрос {current_index + 1}: {question['question']}",
            reply_markup=reply_markup
        )
        context.user_data['start_time'] = datetime.now().isoformat()
    
    except Exception as e:
        await update.callback_query.message.reply_text("Произошла ошибка при загрузке вопроса. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в ask_question: {e}")

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор ответа и обновляет счет."""
    try:
        query = update.callback_query
        await query.answer()
        
        # Получить правильный перемешанный индекс для ответа
        selected_answer_index = int(query.data.split("_")[-1])
        correct_answer_shuffled_index = context.user_data['correct_answer_shuffled_index']
        
        # Предоставить обратную связь по выбранному ответу
        if selected_answer_index == correct_answer_shuffled_index:
            context.user_data['score'] += 1
            feedback = "✅ Правильно!"
        else:
            correct_option = context.user_data['shuffled_questions'][context.user_data['current_question_index']]['options'][correct_answer_shuffled_index]
            feedback = f"❌ Неправильно! Правильный ответ: {correct_option}"

        # Удалить старое сообщение с вопросом
        await query.message.delete()

        # Перейти к следующему вопросу
        context.user_data['current_question_index'] += 1

        # Показать обратную связь и следующий вопрос
        await query.message.reply_text(feedback)
        await ask_question(update, context)

    except Exception as e:
        await update.callback_query.message.reply_text("Произошла ошибка при обработке вашего ответа. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в handle_answer: {e}")

async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатия кнопки отмены."""
    query = update.callback_query
    await query.answer()

    # Очистить данные викторины из контекста пользователя
    context.user_data.clear()
    
    await query.message.reply_text("Сеанс викторины отменен.")

async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Завершить викторину, показать итоговый балл пользователя, сохранить сеанс и предоставить опции для повторной игры или завершения сеанса."""
    try:
        score = context.user_data['score']
        total_questions = len(quiz_data['categories'][context.user_data['category_index']]['questions'])

        # Сохранить данные сеанса
        chat_id = update.effective_chat.id
        quiz_name = context.user_data.get('quiz_name', context.user_data.get('category_index'))
        start_time = datetime.fromisoformat(context.user_data.get('start_time'))
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        current_question_index = context.user_data.get('current_question_index', 0)

        # Создать и сохранить сеанс QuizSession
        quiz_session_to_save = QuizSession(chat_id, quiz_name, start_time, end_time, score, duration, current_question_index)
        save_session_to_user(quiz_session_to_save)

        # Показать итоговый балл
        await update.callback_query.message.reply_text(f"Викторина завершена! Ваш счет: {score}/{total_questions}")

        # Показать опции завершения игры (например, повторная игра или завершение сеанса)
        await show_end_game_keyboard(update, context)

    except Exception as e:
        await update.callback_query.message.reply_text("Произошла ошибка при завершении викторины. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в end_quiz: {e}")

async def handle_quiz_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка выбора категории викторины."""
    query = update.callback_query
    await query.answer()
    
    try:
        category_index = int(query.data.split("_")[-1])
        context.user_data['category_index'] = category_index
        context.user_data['quiz_name'] = quiz_data['categories'][category_index]['name']
        context.user_data['quiz_in_progress'] = True

        await query.message.reply_text(f"Выбранная категория: {quiz_data['categories'][category_index]['name']}")
        await ask_question(update, context)
    
    except Exception as e:
        await query.message.reply_text("Произошла ошибка при выборе категории викторины. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в handle_quiz_selection: {e}")

async def handle_play_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатия кнопки повторной игры для перезапуска викторины."""
    query = update.callback_query
    await query.answer()

    try:
        # Сброс данных пользователя для сеанса викторины
        context.user_data['current_question_index'] = 0
        context.user_data['score'] = 0
        context.user_data['quiz_in_progress'] = True
        
        await ask_question(update, context)
    
    except Exception as e:
        await query.message.reply_text("Произошла ошибка при перезапуске викторины. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в handle_play_again: {e}")

async def handle_choose_another_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатия кнопки выбора другой викторины для начала нового выбора викторины."""
    query = update.callback_query
    await query.answer()

    try:
        # Очистить предыдущие данные викторины
        context.user_data.clear()
        
        # Показать опции начала игры для выбора новой категории викторины
        await show_other_categories_keyboard(update, context)
    
    except Exception as e:
        if query.message:
            await query.message.reply_text("Произошла ошибка при запуске нового выбора викторины. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в handle_choose_another_quiz: {e}")

async def quiz_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий кнопок для действий викторины и навигации по вопросам."""
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "choose_another_quiz":
            # Показать категории снова для начала новой викторины
            await show_start_game_keyboard(update, context)
            context.user_data['quiz_in_progress'] = True

    except Exception as e:
        await query.edit_message_text("Произошла ошибка во время викторины. Пожалуйста, свяжитесь с поддержкой.")
        logging.error(f"Ошибка в quiz_button: {e}")

async def end_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /end для завершения сеанса."""
    # Очистить данные викторины из контекста пользователя
    context.user_data.clear()
    await update.message.reply_text("Сеанс викторины завершен.")

def setup_session_handlers(application: application) -> None:
    application.add_handler(CommandHandler("quiz_start", quiz_start))
    application.add_handler(CommandHandler("continue", continue_quiz))
    application.add_handler(CommandHandler("end", end_session))  # Обработчик для команды /end
    application.add_handler(CommandHandler("cancel", end_session))  # Обработчик для команды /cancel
    application.add_handler(CallbackQueryHandler(handle_quiz_selection, pattern="^choose_category_\\d+$"))
    application.add_handler(CallbackQueryHandler(ask_question, pattern="^play_quiz$"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_\\d+$"))
    application.add_handler(CallbackQueryHandler(handle_cancel, pattern="^cancel$"))
    application.add_handler(CallbackQueryHandler(handle_play_again, pattern="^play_again$"))
    application.add_handler(CallbackQueryHandler(handle_choose_another_quiz, pattern="^choose_another_quiz"))
    application.add_handler(CallbackQueryHandler(quiz_button, pattern="^(play_quiz|end_session|choose_category_\\d+|play_again|continue_quiz)$"))