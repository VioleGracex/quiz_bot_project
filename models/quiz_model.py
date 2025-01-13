from datetime import datetime

from utils.db_utils import init_sessions_db, save_session

class QuizSession:
    def __init__(self, chat_id, quiz_name):
        self.chat_id = chat_id
        self.quiz_name = quiz_name
        self.start_time = datetime.now()
        self.end_time = None
        self.score = 0
        self.duration = None
        self.current_question_index = 0

        # Initialize the session in the database
        init_sessions_db()
        self.save_to_db()

    def save_to_db(self):
        # Save the session data to the database
        save_session(
            self.chat_id,
            self.quiz_name,
            self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None,
            self.score,
            self.duration,
            self.current_question_index
        )

    def end_session(self):
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.save_to_db()  # Update session in the database with the end time and duration

    def update_score(self, new_score):
        self.score = new_score
        self.save_to_db()

    def update_current_question_index(self, new_index):
        self.current_question_index = new_index
        self.save_to_db()