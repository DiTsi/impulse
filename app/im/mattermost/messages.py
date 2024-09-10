import json
from time import sleep

import requests

from app.im.colors import status_colors
from app.im.mattermost.config import mattermost_headers, mattermost_request_delay


def mattermost_send_message(url, channel_id, message, attachment):
    payload = {
        'channel_id': channel_id,
        'message': message,
        'props': {
            'attachments': [
                {
                    'fallback': 'test',
                    'text': attachment,
                    'color': status_colors['closed']
                }
            ]
        }
    }
    response = requests.post(f'{url}/api/v4/posts', headers=mattermost_headers, data=json.dumps(payload))
    sleep(mattermost_request_delay)
    return response.json().get('ts')
