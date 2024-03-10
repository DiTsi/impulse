import requests

from app.channel import Channel
from config import slack_token


class SlackChannel(Channel):
    def __init__(self, id_, name, message_template, topics):
        super().__init__(id_, name, message_template, 'slack', topics)


class SlackChannels:
    def __init__(self, channels_list):
        self.channels = channels_list
        self.channels_by_id = {c.id: SlackChannel(
            c.id,
            c.name,
            c.message_template,
            c.topics,
        ) for c in self.channels}
        self.channels_by_name = {c.name: SlackChannel(
            c.id,
            c.name,
            c.message_template,
            c.topics,
        ) for c in self.channels}

    def get_by_id(self, id_):
        return self.channels_by_id.get(id_)

    def get_by_name(self, name):
        return self.channels_by_name.get(name)


def get_private_channels():
    url = 'https://slack.com/api/conversations.list'
    headers = {'Authorization': f'Bearer {slack_token}'}
    try:
        response = requests.get(url, headers=headers, params={'types': 'private_channel'})
        data = response.json()
        channels = data.get('app', [])
        return channels
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve channel list: {e}') #!
        return []


def get_public_channels():
    url = 'https://slack.com/api/conversations.list'
    headers = {'Authorization': f'Bearer {slack_token}'}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        channels = data.get('app', [])
        return channels
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve channel list: {e}') #!
        return []


def get_channels_list():
    all_bot_channels = get_public_channels() + get_private_channels()
    return SlackChannels(
        [SlackChannel(c.get('id'), c.get('name'), c.get('message_template'), c.get('topics')) for c in all_bot_channels]
    )


existing_channels = get_channels_list()
