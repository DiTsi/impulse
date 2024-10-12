class User:
    def __init__(self, name, slack_id=None):
        self.name = name
        self.id = slack_id
        self.exists = True if slack_id is not None else False
        self.defined = True

    def __repr__(self):
        return self.name
