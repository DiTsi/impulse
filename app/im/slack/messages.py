import json
from time import sleep

import requests

from .config import slack_headers, slack_request_delay


def slack_send_message(url, channel_id, message):
    payload = {
        'channel': channel_id,
        'text': message,
        'unfurl_links': False,
        'unfurl_media': False
    }
    response = requests.post(f'{url}/api/chat.postMessage', headers=slack_headers, data=json.dumps(payload))
    sleep(slack_request_delay)
    return response.json().get('ts')
