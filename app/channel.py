class Channel:
    def __init__(self, id_, name, message_template, type_, actions):
        self.id = id_
        self.name = name
        self.message_template = message_template
        self.type = type_
        self.actions = actions

    def __repr__(self):
        return self.name
