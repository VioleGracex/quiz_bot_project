import logging
import os
import sqlite3
from models.user_model import User
from typing import Optional

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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            quiz_name TEXT,
            start_time TEXT,
            end_time TEXT,
            score INTEGER,
            duration REAL,
            current_question_index INTEGER,
            highest_score INTEGER,
            FOREIGN KEY (chat_id) REFERENCES users (chat_id)
        )
    ''')

    connection.commit()
    connection.close()

# Database functions
def add_user_to_db(user: User):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (chat_id, name, job, phone_number, email, privacy_accepted) VALUES (?, ?, ?, ?, ?, ?)",
        (user.chat_id, user.name, user.job, user.phone_number, user.email, user.privacy_accepted)
    )
    connection.commit()
    connection.close()

def get_user_by_chat_id(chat_id: int):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    connection.close()
    if result:
        return User(*result)
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
    connection.commit()
    connection.close()

def save_session(chat_id, quiz_name, start_time, end_time, score, duration, current_question_index):
    logging.debug(f"Saving session: chat_id={chat_id}, quiz_name={quiz_name}, start_time={start_time}, end_time={end_time}, score={score}, duration={duration}, current_question_index={current_question_index}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get the current highest score from the database for this chat_id
    cursor.execute("SELECT highest_score FROM sessions WHERE chat_id = ? ORDER BY id DESC LIMIT 1", (chat_id,))
    result = cursor.fetchone()

    highest_score = score
    if result:
        # If a session exists, compare and update the highest score if necessary
        highest_score = max(result[0], score)

    # Insert a new session ensuring it's unique (id will auto-increment)
    cursor.execute(""" 
    INSERT INTO sessions (chat_id, quiz_name, start_time, end_time, score, duration, current_question_index, highest_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (chat_id, quiz_name, start_time, end_time, score, duration, current_question_index, highest_score))

    conn.commit()
    conn.close()



def get_session_by_id(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()
    
    conn.close()
    return session

def get_sessions_by_user(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sessions WHERE chat_id = ? ORDER BY id DESC", (chat_id,))
    sessions = cursor.fetchall()
    
    conn.close()
    return sessions

def get_user_session_count(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE chat_id = ?", (chat_id,))
    session_count = cursor.fetchone()[0]  # Get the first element of the result (the count)
    
    conn.close()
    return session_count

def get_global_score():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(score) FROM sessions")
    global_score = cursor.fetchone()[0]  # Sum of all scores across all sessions
    
    conn.close()
    return global_score if global_score is not None else 0  # Return 0 if there are no sessions

def get_highest_score(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT highest_score FROM sessions WHERE chat_id = ? ORDER BY id DESC LIMIT 1", (chat_id,))
    highest_score = cursor.fetchone()[0]
    
    conn.close()
    return highest_score

def get_current_question_index(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT current_question_index FROM sessions WHERE chat_id = ? ORDER BY id DESC LIMIT 1", (chat_id,))
    current_question_index = cursor.fetchone()
    current_question_index = current_question_index[0] if current_question_index else 0
    
    conn.close()
    return current_question_index
