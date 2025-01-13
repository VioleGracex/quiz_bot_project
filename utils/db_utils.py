import os
import sqlite3
from models.user_model import User
from typing import Optional

# Directory setup for database storage
DB_DIRECTORY = "data"
DB_FILE = "quizzer_users.db"
DB_PATH = os.path.join(DB_DIRECTORY, DB_FILE)

# Ensure the data directory exists
os.makedirs(DB_DIRECTORY, exist_ok=True)

# Database setup
def create_users_table():
    print(f"Creating table at {DB_PATH}")
    connection = sqlite3.connect(DB_PATH)
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

def delete_user_from_db(chat_id: int):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
    connection.commit()
    connection.close()
