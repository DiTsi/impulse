class User:
    def __init__(self, name, user_id, username):
        self.name = name
        self.id = user_id
        self.exists = True if user_id is not None else False
        self.username = username

    def __repr__(self):
        return self.username
