import requests

from config import slack_token


class Channel:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class Channels:
    def __init__(self, channels_list):
        self.channels = channels_list
        self.channels_by_id = {c.id: Channel(c.id, c.name) for c in self.channels}
        self.channels_by_name = {c.name: (Channel(c.id, c.name)) for c in self.channels}

    def get_by_id(self, id):
        return self.channels_by_id.get(id)

    def get_by_name(self, name):
        return self.channels_by_name.get(name)


def get_private_channels():
    url = 'https://slack.com/api/conversations.list'
    headers = {'Authorization': f'Bearer {slack_token}'}
    try:
        response = requests.get(url, headers=headers, params={'types': 'private_channel'})
        data = response.json()
        channels = data.get('channels', [])
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
        channels = data.get('channels', [])
        return channels
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve channel list: {e}') #!
        return []


def get_channels_list():
    all_bot_channels = get_public_channels() + get_private_channels()
    return Channels(
        [Channel(c.get('id'), c.get('name')) for c in all_bot_channels]
    )


channels = get_channels_list()
