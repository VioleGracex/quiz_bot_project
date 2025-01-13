from datetime import datetime

class QuizSession:
    def __init__(self, user_id, quiz_name):
        self.user_id = user_id
        self.quiz_name = quiz_name
        self.start_time = datetime.now()
        self.end_time = None
        self.score = 0
        self.duration = None
        self.current_question_index = 0

    def end_session(self):
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
