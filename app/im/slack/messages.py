import json

import requests

from .config import slack_headers


def slack_send_message(url, channel_id, message):
    payload = {
        'channel': channel_id,
        'text': message,
        'mrkdwn_in': ['text'],
        'unfurl_links': False,
        'unfurl_media': False
    }
    response = requests.post(f'{url}/api/chat.postMessage', headers=slack_headers, data=json.dumps(payload))
    return response.json().get('ts')
