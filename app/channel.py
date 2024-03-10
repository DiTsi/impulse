class Channel:
    def __init__(self, id_, name, message_template, type_, threads):
        self.id = id_
        self.name = name
        self.message_template = message_template
        self.type = type_
        self.threads = threads

    def __repr__(self):
        return self.name
