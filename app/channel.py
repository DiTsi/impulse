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
    def __init__(self, public_channels, channels_dict):
        self.channels_by_id = {}
        self.channels_by_name = {}

        non_existing_channels = []
        for channel_name in channels_dict.keys():
            try:
                self.channels_by_id[public_channels[channel_name]['id']] = SlackChannel(
                    public_channels[channel_name]['id'],
                    channel_name,
                    channels_dict[channel_name]['message_template'],
                    channels_dict[channel_name]['chains'],
                )
            except KeyError:
                print(f'Channel \'{channel_name}\' from config.yml does not exist in Slack') #!
                non_existing_channels.append(channel_name)

        for c in non_existing_channels:
            del channels_dict[c]

        for channel_name in channels_dict.keys():
            self.channels_by_name[channel_name] = SlackChannel(
                public_channels[channel_name]['id'],
                channel_name,
                channels_dict[channel_name]['message_template'],
                channels_dict[channel_name]['chains'],
            )

    def get_by_chain(self, chain):
        for name in self.channels_by_name.keys():
            if chain in self.channels_by_name[name].chains:
                return self.channels_by_name[name]
        print(f'There is no channel containing chain \'{chain}\'') # error
        return None
