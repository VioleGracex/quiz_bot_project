from datetime import datetime
import os
import sqlite3
from typing import Optional
from models.user_model import User
from models.quiz_model import QuizSession

def create_connection():
    return sqlite3.connect('data/db.sqlite3')

import sqlite3

def register_user(chat_id, user_data):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        # Check if user already exists
        cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", (chat_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # User already exists, update their data if necessary
            cursor.execute("""
                UPDATE users
                SET name = ?, email = ?, job = ?, telephone = ?
                WHERE chat_id = ?
            """, (user_data['name'], user_data['email'], user_data['job'], user_data['phone'], chat_id))
        else:
            # User does not exist, insert new user
            cursor.execute("""
                INSERT INTO users (chat_id, name, email, job, telephone) 
                VALUES (?, ?, ?, ?, ?)
            """, (chat_id, user_data['name'], user_data['email'], user_data['job'], user_data['phone']))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()  # Ensure the connection is always closed


def get_user_by_chat_id(chat_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(*user_data)
    return None

def create_quiz_session(user_id: int, quiz_name: str) -> Optional[QuizSession]:
    if not quiz_name:
        return None  # Log an error here if necessary, indicating the invalid quiz_name
    
    try:
        conn = create_connection()  # Ensure that create_connection() is implemented correctly
        cursor = conn.cursor()

        # Prepare the insert query with the current timestamp
        cursor.execute("""
            INSERT INTO quiz_sessions (user_id, quiz_name, score, start_time) 
            VALUES (?, ?, ?, ?)
        """, (user_id, quiz_name, 0, datetime.now()))

        conn.commit()

        # Retrieve the inserted session data and return a QuizSession object
        cursor.execute("SELECT id FROM quiz_sessions WHERE user_id = ? AND quiz_name = ?", (user_id, quiz_name))
        quiz_session_id = cursor.fetchone()[0]  # Assuming 'id' is the primary key

        conn.close()

        # Return a QuizSession object initialized with the database values
        return QuizSession(user_id=user_id, quiz_name=quiz_name)

    except Exception as e:
        print(f"Error creating quiz session: {e}")
        return None

def initialize_db():
    """Initialize the database with tables if they do not exist."""
    if not os.path.exists('data/db.sqlite3'):
        # Database file doesn't exist, create it and the tables
        conn = create_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE,
                name TEXT,
                email TEXT,
                job TEXT,
                telephone TEXT
            )
        ''')
        
        # Create quiz_sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                quiz_name TEXT,
                score INTEGER,
                start_time DATETIME,
                end_time DATETIME,
                duration INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()

initialize_db()