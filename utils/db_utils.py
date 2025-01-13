import os
import sqlite3
from models.user_model import User
from typing import Optional

# Directory setup for database storage
DB_DIRECTORY = "data"
DB_USERS = "quizzer_users.db"
DB_SESSIONS= "quizzer_user_sessions.db"
DB_USERS_PATH = os.path.join(DB_DIRECTORY, DB_USERS)
DB_SESSIONS_PATH = os.path.join(DB_DIRECTORY, DB_SESSIONS)

# Ensure the data directory exists
os.makedirs(DB_DIRECTORY, exist_ok=True)

# Database setup
def init_users_db():
    print(f"Creating table at {DB_USERS_PATH}")
    connection = sqlite3.connect(DB_USERS_PATH)
    cursor = connection.cursor()
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
    connection.commit()
    connection.close()


# Database functions
def add_user_to_db(user: User):
    connection = sqlite3.connect(DB_USERS_PATH)
    cursor = connection.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (chat_id, name, job, phone_number, email, privacy_accepted) VALUES (?, ?, ?, ?, ?, ?)",
        (user.chat_id, user.name, user.job, user.phone_number, user.email, user.privacy_accepted)
    )
    connection.commit()
    connection.close()

def get_user_by_chat_id(chat_id: int):
    connection = sqlite3.connect(DB_USERS_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    connection.close()
    if result:
        return User(*result)
    return None

def is_user_in_db(chat_id: int) -> bool:
    """Checks if a user is already in the database."""
    connection = sqlite3.connect(DB_USERS_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    connection.close()
    
    print(f"Checking if user {chat_id} exists: {result is not None}")  # Log the result of the query
    
    return result is not None  # Returns True if user exists, otherwise False


def delete_user_from_db(chat_id: int):
    connection = sqlite3.connect(DB_USERS_PATH)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
    connection.commit()
    connection.close()



# Initialize the database and table
def init_sessions_db():
    conn = sqlite3.connect(DB_SESSIONS_PATH)
    cursor = conn.cursor()
    
    # Create table if not exists with a new field for highest_score
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_sessions (
        chat_id INTEGER PRIMARY KEY,
        quiz_name TEXT,
        start_time TEXT,
        end_time TEXT,
        score INTEGER,
        duration REAL,
        current_question_index INTEGER,
        highest_score INTEGER
    )
    """)
    conn.commit()
    conn.close()

# Save the quiz session to the database
def save_session(chat_id, quiz_name, start_time, end_time, score, duration, current_question_index):
    conn = sqlite3.connect(DB_SESSIONS_PATH)
    cursor = conn.cursor()
    
    # Fetch the current highest score
    cursor.execute("SELECT highest_score FROM quiz_sessions WHERE chat_id = ?", (chat_id,))
    current_highest_score = cursor.fetchone()
    current_highest_score = current_highest_score[0] if current_highest_score else 0
    
    # Update the highest score if the new score is greater
    new_highest_score = max(current_highest_score, score)
    
    cursor.execute("""
    INSERT OR REPLACE INTO quiz_sessions (chat_id, quiz_name, start_time, end_time, score, duration, current_question_index, highest_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (chat_id, quiz_name, start_time, end_time, score, duration, current_question_index, new_highest_score))
    
    conn.commit()
    conn.close()

# Fetch the quiz session for a specific chat_id
def get_session(chat_id):
    conn = sqlite3.connect(DB_SESSIONS_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM quiz_sessions WHERE chat_id = ?", (chat_id,))
    session = cursor.fetchone()
    
    conn.close()
    return session

# Get the number of sessions played by a user (based on chat_id)
def get_user_session_count(chat_id):
    conn = sqlite3.connect(DB_SESSIONS_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM quiz_sessions WHERE chat_id = ?", (chat_id,))
    session_count = cursor.fetchone()[0]  # Get the first element of the result (the count)
    
    conn.close()
    return session_count

# Get the global score (sum of all session scores)
def get_global_score():
    conn = sqlite3.connect(DB_SESSIONS_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(score) FROM quiz_sessions")
    global_score = cursor.fetchone()[0]  # Sum of all scores across all sessions
    
    conn.close()
    return global_score if global_score is not None else 0  # Return 0 if there are no sessions

# Get the highest score (now stored in the `highest_score` field)
def get_highest_score(chat_id):
    conn = sqlite3.connect(DB_SESSIONS_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT highest_score FROM quiz_sessions WHERE chat_id = ?", (chat_id,))
    highest_score = cursor.fetchone()[0]
    
    conn.close()
    return highest_score

# Get the current question index for a specific chat_id
def get_current_question_index(chat_id):
    conn = sqlite3.connect(DB_SESSIONS_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT current_question_index FROM quiz_sessions WHERE chat_id = ?", (chat_id,))
    current_question_index = cursor.fetchone()
    current_question_index = current_question_index[0] if current_question_index else 0
    
    conn.close()
    return current_question_index

# Save the quiz session to the database
def save_session(chat_id, quiz_name, category_name, start_time, end_time, score, duration, current_question_index):
    conn = sqlite3.connect(DB_SESSIONS_PATH)
    cursor = conn.cursor()
    
    # Fetch the current highest score for the specific category
    cursor.execute("SELECT highest_score FROM quiz_sessions WHERE chat_id = ? AND category_name = ?", (chat_id, category_name))
    current_highest_score = cursor.fetchone()
    current_highest_score = current_highest_score[0] if current_highest_score else 0
    
    # Update the highest score if the new score is greater
    new_highest_score = max(current_highest_score, score)
    
    cursor.execute("""
    INSERT OR REPLACE INTO quiz_sessions (chat_id, quiz_name, category_name, start_time, end_time, score, duration, current_question_index, highest_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (chat_id, quiz_name, category_name, start_time, end_time, score, duration, current_question_index, new_highest_score))
    
    conn.commit()
    conn.close()