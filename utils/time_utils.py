from datetime import datetime

def get_current_time():
    return datetime.now()

def calculate_duration(start_time, end_time):
    return (end_time - start_time).total_seconds()
