import json
from time import sleep

import requests

from .config import mattermost_headers, mattermost_request_delay


def mattermost_send_message(url, channel_id, message):
    payload = {
        'channel': channel_id,
        'text': message,
        'mrkdwn_in': ['text'],
        'unfurl_links': False,
        'unfurl_media': False
    }
    response = requests.post(f'{url}/api/chat.postMessage', headers=mattermost_headers, data=json.dumps(payload))
    sleep(mattermost_request_delay)
    return response.json().get('ts')
