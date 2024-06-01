class Channel:
    def __init__(self, id_, name, message_template, type_):
        self.id = id_
        self.name = name
        self.message_template = message_template
        self.type = type_

    def __repr__(self):
        return f'{self.name} ({self.type})'


# def generate_channels(route_dict, slack_channels):
#     logger.debug(f'Creating Channels')
#     channels = {}
#     for channel in route_dict.items():
#         channel_name = channel[0]
#         # channel_type = channel[1]['type']
#         # channel_template = channel[1]['message_template']
#         if channel_type == 'slack':
#             try:
#                 channel_id = slack_channels[channel_name]['id']
#                 channels[channel_id] = Channel(channel_id, channel_name, channel_template, channel_type)
#             except KeyError:
#                 logger.warning(f'No public channel \'{channel_name}\' in Slack')
#     logger.debug(f'Channels created')
#     return channels
