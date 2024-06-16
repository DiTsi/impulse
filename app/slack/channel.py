class Channel:
    def __init__(self, id_, name, message_template, type_):
        self.id = id_
        self.name = name
        self.message_template = message_template
        self.type = type_

    def __repr__(self):
        return f'{self.name} ({self.type})'
