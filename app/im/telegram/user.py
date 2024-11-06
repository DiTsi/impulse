class User:
    def __init__(self, id_, name, username, exists=False):
        self.id = id_
        self.name = name
        self.username = username
        self.exists = exists

    def __repr__(self):
        return self.username
