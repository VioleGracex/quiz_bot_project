import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional

# Directory setup for database storage
DB_DIRECTORY = "data"
DB_NAME = "quizzer.db"
DB_PATH = os.path.join(DB_DIRECTORY, DB_NAME)

# Ensure the data directory exists
os.makedirs(DB_DIRECTORY, exist_ok=True)

# Database setup
def init_db():
    print(f"Creating tables at {DB_PATH}")
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            name TEXT,
            job TEXT,
            phone_number TEXT,
            email TEXT,
            privacy_accepted INTEGER DEFAULT 0  -- 0 = not accepted, 1 = accepted
        )
    ''')

    # Create sessions table with session ID and foreign key reference to users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            chat_id INTEGER,
            quiz_name TEXT,
            start_time TEXT,
            end_time TEXT,
            score INTEGER,
            duration REAL,
            current_question_index INTEGER,
            FOREIGN KEY (chat_id) REFERENCES users (chat_id)
        )
    ''')

    connection.commit()
    connection.close()

# Initialize the database
init_db()

# Database functions
def add_user_to_db(user):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (chat_id, name, job, phone_number, email, privacy_accepted) VALUES (?, ?, ?, ?, ?, ?)",
        (user.chat_id, user.name, user.job, user.phone_number, user.email, user.privacy_accepted)
    )
    connection.commit()
    connection.close()

def get_user_chat_id(chat_id):
    """Retrieve the chat_id for a given user_id from the database."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()

    connection.close()

    if result:
        return result[0]
    else:
        return None
def get_user_by_chat_id(chat_id: int) -> Optional['User']:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    connection.close()
    if result:
        user = User(*result)
        user.quiz_sessions = get_sessions_by_user(chat_id)
        return user
    return None

def is_user_in_db(chat_id: int) -> bool:
    """Checks if a user is already in the database."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    connection.close()
    
    print(f"Checking if user {chat_id} exists: {result is not None}")  # Log the result of the query
    
    return result is not None  # Returns True if user exists, otherwise False

def delete_user_from_db(chat_id: int):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
    cursor.execute("DELETE FROM sessions WHERE chat_id = ?", (chat_id,))
    connection.commit()
    connection.close()

def save_session_to_user(session: 'QuizSession'):
    """
    Saves a quiz session to the database for a specific user.
    
    :param session: The QuizSession object containing session details.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute(
        '''
        INSERT OR REPLACE INTO sessions (
            session_id, chat_id, quiz_name, start_time, end_time, score, duration, current_question_index
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', 
        (
            session.session_id, session.chat_id, session.quiz_name, session.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            session.end_time.strftime("%Y-%m-%d %H:%M:%S") if session.end_time else None,
            session.score, session.duration, session.current_question_index
        )
    )
    
    connection.commit()
    connection.close()

def get_sessions_by_user(chat_id: int) -> List['QuizSession']:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sessions WHERE chat_id = ? ORDER BY start_time DESC", (chat_id,))
    sessions = cursor.fetchall()
    
    conn.close()
    return [QuizSession.from_db_row(row) for row in sessions]

def get_user_session_count(chat_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE chat_id = ?", (chat_id,))
    session_count = cursor.fetchone()[0]  # Get the first element of the result (the count)
    
    conn.close()
    return session_count

def get_global_score() -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(score) FROM sessions")
    global_score = cursor.fetchone()[0]  # Sum of all scores across all sessions
    
    conn.close()
    return global_score if global_score is not None else 0  # Return 0 if there are no sessions

def get_highest_score(chat_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(score) FROM sessions WHERE chat_id = ?", (chat_id,))
    highest_score = cursor.fetchone()[0]
    
    conn.close()
    return highest_score

def get_current_question_index(chat_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT current_question_index FROM sessions WHERE chat_id = ? ORDER BY start_time DESC LIMIT 1", (chat_id,))
    current_question_index = cursor.fetchone()
    current_question_index = current_question_index[0] if current_question_index else 0
    
    conn.close()
    return current_question_index

class QuizSession:
    def __init__(self, chat_id, quiz_name, start_time=None, end_time=None, score=0, duration=None, current_question_index=0):
        self.session_id = str(uuid.uuid4())  # Generate a unique session ID
        self.chat_id = chat_id
        self.quiz_name = quiz_name
        self.start_time = start_time if start_time else datetime.now()
        self.end_time = end_time
        self.score = score
        self.duration = duration
        self.current_question_index = current_question_index

        self.save_to_db()

    def save_to_db(self):
        # Save the session data to the database
        save_session_to_user(self)

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

    @classmethod
    def from_db_row(cls, row):
        session = cls(row[1], row[2])
        session.session_id = row[0]
        session.start_time = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
        session.end_time = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S") if row[4] else None
        session.score = row[5]
        session.duration = row[6]
        session.current_question_index = row[7]
        return session

class User:
    def __init__(self, chat_id: int, name: str, job: str, phone_number: str, email: str, privacy_accepted: int):
        self.chat_id = chat_id
        self.name = name
        self.job = job
        self.phone_number = phone_number
        self.email = email
        self.privacy_accepted = bool(privacy_accepted)  # Convert to boolean
        self.quiz_sessions = []  # Initialize an empty list of quiz sessions

    def is_privacy_accepted(self):
        return self.privacy_accepted

    def start_quiz_session(self, quiz_name):
        new_session = QuizSession(self.chat_id, quiz_name)
        self.quiz_sessions.append(new_session)
        return new_session

    def get_active_session(self):
        for session in self.quiz_sessions:
            if session.end_time is None:
                return session
        return None

    def end_active_session(self):
        active_session = self.get_active_session()
        if active_session:
            active_session.end_session()

    def update_active_session_score(self, new_score):
        active_session = self.get_active_session()
        if active_session:
            active_session.update_score(new_score)

    def update_active_session_question_index(self, new_index):
        active_session = self.get_active_session()
        if active_session:
            active_session.update_current_question_index(new_index)
            