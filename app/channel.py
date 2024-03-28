class Channel:
    def __init__(self, id_, name, message_template, type_, chains):
        self.id = id_
        self.name = name
        self.message_template = message_template
        self.type = type_
        self.chains = chains

    def __repr__(self):
        return self.name


class SlackChannel(Channel):
    def __init__(self, id_, name, message_template, chains):
        super().__init__(id_, name, message_template, 'slack', chains)


class SlackChannels:
    def __init__(self, channels_list):
        self.channels = channels_list
        self.channels_by_id = {c.get('id'): SlackChannel(
            c.get('id'),
            c.get('name'),
            c.get('message_template'),
            c.get('chains'),
        ) for c in channels_list}
        self.channels_by_name = {c.get('name'): SlackChannel(
            c.get('id'),
            c.get('name'),
            c.get('message_template'),
            c.get('chains'),
        ) for c in channels_list}

    def get_by_id(self, id_):
        return self.channels_by_id.get(id_)

    def get_by_name(self, name):
        return self.channels_by_name.get(name)
