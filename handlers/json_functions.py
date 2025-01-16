import json
import logging
import random

quiz_data = None
def load_quiz_data():
    global quiz_data
    if quiz_data is not None:
        # Return cached quiz data if already loaded
        return quiz_data
    
    try:
        with open('data/quiz_data.json', 'r') as file:
            loaded_data = json.load(file)
        
        # Validate JSON structure
        if not isinstance(loaded_data, dict):
            raise ValueError("Quiz data should be a dictionary.")
        if "categories" not in loaded_data:
            raise KeyError("'categories' key is missing in the quiz data.")
        
        # Validate categories and questions
        for category in loaded_data["categories"]:
            if "name" not in category or "questions" not in category:
                raise KeyError(f"Missing 'name' or 'questions' in category {category}.")
            for question in category["questions"]:
                if "question" not in question or "correct_answer_index" not in question:
                    raise KeyError(f"Missing 'question' or 'correct_answer_index' in question {question}.")
                if "options" not in question:
                    raise KeyError(f"Missing 'options' in question {question}.")
        
        # Store the validated data in a global variable
        quiz_data = loaded_data
        return quiz_data

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading quiz data: {e}")
        return {}

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logging.error(f"Error loading quiz data: {e}")
        raise Exception("Answers were not loaded correctly. Please contact support.")  # Raise an exception for the error