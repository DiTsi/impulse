import json
from time import sleep

import requests

from .config import mattermost_headers


def send_message(url, channel_id, message):
    payload = {
        'channel': channel_id,
        'text': message,
        'mrkdwn_in': ['text'],
        'unfurl_links': False,
        'unfurl_media': False
    }
    response = requests.post(f'{url}/api/chat.postMessage', headers=mattermost_headers, data=json.dumps(payload))
    sleep(0.1)
    return response.json().get('ts')
