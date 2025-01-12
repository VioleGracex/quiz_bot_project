# Telegram Quiz Bot Project

This is a feature-rich Telegram Quiz Bot that allows users to register, choose from multiple quizzes, and tracks the time taken to complete each quiz. Users can switch quizzes, restart, or end them at any time.

## **Features**
- User registration (name, email, job title, phone number)
- Multiple quiz categories
- Time tracking for each quiz
- Score management and session duration display
- SQLite database for storing user data and quiz sessions

---

## **File Structure**
```plaintext
quiz_bot_project/
│
├── main.py                   # Main script to run the bot
├── requirements.txt          # Dependencies list
├── config.py                 # Configuration file for environment variables
├── data/
│   ├── questions.json        # JSON file for quiz questions
│   └── db.sqlite3            # SQLite database for user and quiz data
├── models/
│   ├── user_model.py         # User model for data handling
│   └── quiz_model.py         # Quiz session model for scores and tracking
├── handlers/
│   ├── start_handler.py      # Handles user registration and start command
│   ├── quiz_handler.py       # Quiz logic (questions and answers)
│   └── menu_handler.py       # Handles quiz menu navigation
└── utils/
    ├── db_utils.py           # Database utility functions
    └── time_utils.py         # Helper functions for time calculations
```

---

## **Installation**

### **1. Clone the Repository**
```bash
git clone https://github.com/yourusername/telegram-quiz-bot.git
cd quiz_bot_project
```

### **2. Set Up a Virtual Environment**
```bash
python -m venv venv
```
Activate the virtual environment:
- **Windows (cmd)**: `venv\Scripts\activate`
- **Windows (PowerShell)**: `.env\Scripts\Activate.ps1`
- **Linux/Mac**: `source venv/bin/activate`

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Create a `.env` File**
Create a `.env` file in the root directory and add your Telegram Bot Token:
```
TOKEN=your_telegram_bot_token_here
```

---

## **Usage**
1. Ensure the virtual environment is activated.
2. Run the bot:
   ```bash
   python main.py
   ```
3. Interact with the bot in Telegram:
   - Start the bot with `/start` to register.
   - Use `/menu` to choose a quiz.
   - Follow the on-screen prompts to answer questions.
   - Type `/end` to finish the quiz.

---

## **Database Structure**
### Table: `users`
| Column    | Data Type | Description                    |
|-----------|-----------|--------------------------------|
| id        | INTEGER   | Primary key                    |
| chat_id   | INTEGER   | Unique user identifier         |
| name      | TEXT      | Player's name                  |
| email     | TEXT      | Player's email                 |
| job       | TEXT      | Job title                      |
| telephone | TEXT      | Telephone number               |

### Table: `quiz_sessions`
| Column    | Data Type | Description                             |
|-----------|-----------|-----------------------------------------|
| id        | INTEGER   | Primary key                             |
| user_id   | INTEGER   | Foreign key (links to users.id)         |
| quiz_name | TEXT      | Name of the quiz                        |
| score     | INTEGER   | User’s score                          |
| start_time| DATETIME  | Timestamp of quiz start                 |
| end_time  | DATETIME  | Timestamp of quiz end                   |
| duration  | INTEGER   | Time taken to complete the quiz (secs)  |

---

## **Data File (questions.json)**
```json
{
  "quizzes": {
    "general_knowledge": [
      {
        "question": "What is the capital of Germany?",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "answer": 0
      }
    ],
    "science": [
      {
        "question": "What planet is closest to the sun?",
        "options": ["Earth", "Mars", "Mercury", "Venus"],
        "answer": 2
      }
    ],
    "history": [
      {
        "question": "Who was the first President of the United States?",
        "options": ["Abraham Lincoln", "Thomas Jefferson", "George Washington", "John Adams"],
        "answer": 2
      }
    ],
    "sports": [
      {
        "question": "How many players are there on a soccer team?",
        "options": ["9", "10", "11", "12"],
        "answer": 2
      }
    ]
  }
}
```

---

## **License**
This project is licensed under the MIT License. See `LICENSE` for more information.

