class MessageTemplate:
    def __init__(self, name, text):
        self.name = name
        self.text = text

    def __repr__(self):
        return self.name
