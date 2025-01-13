class User:
    def __init__(self, chat_id: int, name: str, job: str, phone_number: str, email: str, privacy_accepted: int):
        self.chat_id = chat_id
        self.name = name
        self.job = job
        self.phone_number = phone_number
        self.email = email
        self.privacy_accepted = bool(privacy_accepted)  # Convert to boolean

    # You can also implement methods like:
    def is_privacy_accepted(self):
        return self.privacy_accepted
