import json
from time import sleep

import requests

from .config import slack_headers, slack_request_delay
from ..colors import status_colors


def slack_send_message(url, channel_id, message, attachment):
    payload = {
        'channel': channel_id,
        'text': message,
        'unfurl_links': False,
        'unfurl_media': False,
        'attachments': [
            {
                'color': status_colors['closed'],
                'text': attachment,
                'mrkdwn_in': ['text'],
            }
        ]
    }
    response = requests.post(f'{url}/api/chat.postMessage', headers=slack_headers, data=json.dumps(payload))
    sleep(slack_request_delay)
    return response.json().get('ts')
