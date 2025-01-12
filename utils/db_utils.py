from datetime import datetime
import os
import sqlite3
from models.user_model import User
from models.quiz_model import QuizSession

def create_connection():
    return sqlite3.connect('data/db.sqlite3')

def register_user(chat_id, user_data):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (chat_id, name, email, job, telephone) VALUES (?, ?, ?, ?, ?)",
                   (chat_id, user_data['name'], user_data['email'], user_data['job'], user_data['phone']))
    conn.commit()
    conn.close()

def get_user_by_chat_id(chat_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(*user_data)
    return None

def create_quiz_session(user_id, quiz_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quiz_sessions (user_id, quiz_name, score, start_time) VALUES (?, ?, ?, ?)",
                   (user_id, quiz_name, 0, datetime.now()))
    conn.commit()
    conn.close()


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

