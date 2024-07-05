import json

import requests

from .config import headers, url


def send_message(channel_id, message):
    payload = {
        'channel': channel_id,
        'text': message,
        'mrkdwn_in': ['text'],
        'unfurl_links': False,
        'unfurl_media': False
    }
    response = requests.post(f'{url}/api/chat.postMessage', headers=headers, data=json.dumps(payload))
    return response.json().get('ts')
