import json
import os

def get_question_data(quiz_name):
    # Define the path to your JSON file
    file_path = os.path.join(os.path.dirname(__file__), '../data/questions.json')

    # Read the questions from the JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Return the questions for the requested quiz
    return data["quizzes"].get(quiz_name, [])
