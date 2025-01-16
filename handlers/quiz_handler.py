
async def quiz_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses for quiz actions and navigating through questions."""
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "end_session":
            await query.edit_message_text("Thanks for playing! We hope you enjoyed the quiz. Check out our other products!")
            context.user_data.clear()
            return

        elif query.data == "play_quiz":
            # Show categories to choose from
            
            keyboard = [
                [InlineKeyboardButton(f"{category['name']} - {len(category['questions'])} questions", callback_data=f"choose_category_{i}")]
                for i, category in enumerate(quiz_data["categories"])
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Please choose a category to start the quiz:", reply_markup=reply_markup)
            context.user_data['quiz_in_progress'] = True
            #after choosing category save it in content.user.quiz_name
        elif query.data == "continue_quiz":
            # Check if there's an ongoing quiz and continue
            if 'category_index' not in context.user_data or 'current_question_index' not in context.user_data:
                await query.edit_message_text("No quiz in progress. Please start a new quiz.")
                return

            category_index = context.user_data['category_index']
            current_question_index = context.user_data['current_question_index']
            category = quiz_data["categories"][category_index]

            # If there are remaining questions, ask the next question
            if current_question_index < len(category['questions']):
                await ask_question(update, context)
            else:
                # If no questions are left, show the result
                await query.edit_message_text(f"Congratulations! You've completed the quiz in the '{category['name']}' category.")
                await query.message.reply_text("Would you like to play again?", reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Play Again", callback_data='play_again')]
                ]))

        elif query.data == "choose_another_quiz":
            # Show categories again to start a new quiz
            await show_start_game_keyboard(update, context)
            context.user_data['quiz_in_progress'] = True

        elif query.data.startswith("choose_category_"):
            # Get the category index and start the quiz
            category_index = int(query.data.split("_")[-1])
            category = quiz_data["categories"][category_index]
            
            # Save the category index and name in user data
            context.user_data['category_index'] = category_index
            context.user_data['quiz_name'] = category['name']
            context.user_data['current_question_index'] = 0
            context.user_data['score'] = 0
            
            # Start the quiz with the first question
            await query.edit_message_text(f"Starting quiz in the '{category['name']}' category. Good luck!")
            await ask_question(update, context)

        elif query.data == "play_again":
            # Get the last category played from user data and restart the quiz
            category_index = context.user_data.get('category_index')
            if category_index is not None:              
                category = quiz_data["categories"][category_index]
                
                # Reset score and question index, and start the quiz again
                del context.user_data['shuffled_questions']
                context.user_data['current_question_index'] = 0
                context.user_data['score'] = 0
                context.user_data['quiz_name'] = category['name']
                await query.edit_message_text(f"Starting quiz again in the '{category['name']}' category. Good luck!")
                await ask_question(update, context)
            else:
                await query.edit_message_text("No category found. Please choose a category to start the quiz.")

    except Exception as e:
        await query.edit_message_text("There was an issue during the quiz. Please contact support.")
        logging.error(f"Error in quiz_button: {e}")

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the current question, randomize question and answer order, and handle the user's response."""
    try:
 
        category = quiz_data["categories"][context.user_data['category_index']]
        
        # Shuffle questions on the first access
        if 'shuffled_questions' not in context.user_data:
            shuffled_questions = category['questions'][:]
            random.shuffle(shuffled_questions)
            context.user_data['shuffled_questions'] = shuffled_questions
            context.user_data['current_question_index'] = 0
            context.user_data['score'] = 0  # Initialize score
        
        questions = context.user_data['shuffled_questions']
        current_index = context.user_data['current_question_index']

        # Check if we've run out of questions
        if current_index >= len(questions):
            await end_quiz(update, context)
            return

        question = questions[current_index]
        options = question.get("options", [])

        # Shuffle the order of options and store correct answer index
        option_indices = list(range(len(options)))
        random.shuffle(option_indices)
        shuffled_options = [options[i] for i in option_indices]
        correct_answer_shuffled_index = option_indices.index(question['correct_answer_index'])
        context.user_data['correct_answer_shuffled_index'] = correct_answer_shuffled_index  # Track for correctness check

        keyboard = [[InlineKeyboardButton(opt, callback_data=f"answer_{i}")] for i, opt in enumerate(shuffled_options)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        logging.info(f"Question: {question['question']} with shuffled options: {shuffled_options}")
        await update.callback_query.message.reply_text(
            f"Question {current_index + 1}: {question['question']}",
            reply_markup=reply_markup
        )
        context.user_data['start_time'] = datetime.now().isoformat()
    
    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue loading the question. Please contact support.")
        logging.error(f"Error in ask_question: {e}")

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the answer selection and updates the score."""
    try:
        query = update.callback_query
        await query.answer()
        
        # Retrieve the correct shuffled index for the answer
        selected_answer_index = int(query.data.split("_")[-1])
        correct_answer_shuffled_index = context.user_data['correct_answer_shuffled_index']
        
        # Provide feedback on the selected answer
        if selected_answer_index == correct_answer_shuffled_index:
            context.user_data['score'] += 1
            feedback = "✅ Correct!"
        else:
            correct_option = context.user_data['shuffled_questions'][context.user_data['current_question_index']]['options'][correct_answer_shuffled_index]
            feedback = f"❌ Incorrect! The correct answer was: {correct_option}"

        # Delete the old question message
        await query.message.delete()

        # Move to the next question
        context.user_data['current_question_index'] += 1

        # Show feedback and next question
        await query.message.reply_text(feedback)
        await ask_question(update, context)

    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue handling your answer. Please contact support.")
        logging.error(f"Error in handle_answer: {e}")       
async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End the quiz, show the user's final score, save the session, and provide options to play again or end the session."""
    try:
        score = context.user_data['score']
        total_questions = len(load_quiz_data()['categories'][context.user_data['category_index']]['questions'])

        # Save the session data
        chat_id = update.effective_chat.id
        quiz_name = context.user_data.get('quiz_name', context.user_data.get('category_index'))
        start_time = context.user_data.get('start_time')
        end_time = datetime.now().isoformat()
        duration = (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds() / 60
        current_question_index = context.user_data.get('current_question_index', 0)

        # Save the session to the database
        save_session_to_user(chat_id, quiz_name, start_time, end_time, score, duration, current_question_index)

        # Show the final score
        await update.callback_query.message.reply_text(f"Quiz finished! Your score: {score}/{total_questions}")

        # Show the end game options (e.g., play again or end session)
        await show_end_game_keyboard(update, context)

    except Exception as e:
        await update.callback_query.message.reply_text("There was an issue ending the quiz. Please contact support.")
        logging.error(f"Error in end_quiz: {e}")
async def handle_end_game_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the end game action based on user choice."""
    try:
        query = update.callback_query
        await query.answer()

        chat_id = update.effective_chat.id
        quiz_name = context.user_data.get('quiz_name', context.user_data.get('category_index'))
        start_time = context.user_data.get('start_time')
        end_time = datetime.now().isoformat()
        score = context.user_data.get('score', 0)
        duration = (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds() / 60
        current_question_index = context.user_data.get('current_question_index', 0)

        # Debug log for session data
        logging.debug(f"Handling end game for chat_id: {chat_id}, quiz_name: {quiz_name}, score: {score}, duration: {duration}, current_question_index: {current_question_index}")
        logging.debug(f"Session data: start_time={start_time}, end_time={end_time}, score={score}, duration={duration}, current_question_index={current_question_index}")

        if query.data == "play_again":
            # Save session data before starting a new one
            logging.debug("Saving session before play again.")
            save_session_to_user(chat_id, quiz_name, start_time, end_time, score, duration, current_question_index)  # No await needed
            context.user_data.clear()  # Clear previous session data

            # Get the last category played and restart the quiz
            category_index = context.user_data.get('category_index')
            if category_index is not None:
                shuffle_loaded_json()
                category = quiz_data["categories"][category_index]

                # Reset score and question index, and start the quiz again
                context.user_data['current_question_index'] = 0
                context.user_data['score'] = 0
                context.user_data['quiz_in_progress'] = True  # Set new quiz flag
                context.user_data['quiz_name'] = category['name']
                await query.edit_message_text(f"Starting quiz again in the '{category['name']}' category. Good luck!")
                await ask_question(update, context)
            else:
                await query.edit_message_text("No category found. Please choose a category to start the quiz.")

        elif query.data == "choose_another_quiz":
            # Save session data before starting a new quiz selection
            logging.debug("Saving session before choosing another quiz.")
            save_session_to_user(chat_id, quiz_name, start_time, end_time, score, duration, current_question_index)  # No await needed
            context.user_data.clear()  # Clear previous session data

            # Show categories to choose a new quiz
            shuffle_loaded_json()
            keyboard = [
                [InlineKeyboardButton(f"{category['name']} - {len(category['questions'])} questions", callback_data=f"choose_category_{i}")]
                for i, category in enumerate(quiz_data["categories"])
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Please choose a new quiz category:", reply_markup=reply_markup)
            context.user_data['quiz_in_progress'] = True  # Set new quiz flag

        elif query.data == "end_session":
            # Save session data before ending the session
            logging.debug("Saving session before ending the session.")
            save_session_to_user(chat_id, quiz_name, start_time, end_time, score, duration, current_question_index)  # No await needed
            context.user_data.clear()  # Clear all session data
            await query.edit_message_text("Thanks for playing! We hope you enjoyed the quiz.")

    except Exception as e:
        await query.edit_message_text("There was an issue handling the end game action. Please contact support.")
        logging.error(f"Error in handle_end_game_action: {e}")
        logging.debug(f"Exception details: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel the registration and clear user data."""
    if update.message.text.strip().lower() == "cancel":
        await update.message.reply_text("Quiz session cancelled.")
        context.user_data.clear()
