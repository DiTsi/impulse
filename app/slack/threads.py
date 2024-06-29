import json

import requests

from .buttons import buttons
from .config import headers, url, status_colors


def create_thread(channel_id, message, status):
    payload = {
        'channel': channel_id,
        'text': '',
        'attachments': [
            {
                'color': status_colors.get(status),
                'text': message,
                'mrkdwn_in': ['text'],
            },
            {
                'color': status_colors.get(status),
                'text': '',
                'callback_id': 'buttons',
                'actions': [
                    {
                        "name": "chain",
                        "text": buttons['chain']['enabled']['text'],
                        "type": "button",
                        "style": buttons['chain']['enabled']['style']
                    },
                    {
                        "name": "status",
                        "text": buttons['status']['enabled']['text'],
                        "type": "button",
                        "style": buttons['status']['enabled']['style']
                    }
                ]
            }
        ]
    }
    response = requests.post(f'{url}/api/chat.postMessage', headers=headers, data=json.dumps(payload))
    return response.json().get('ts')


# def create_blocked_thread(channel_id, message, status): #! didn't work with "return modified_message, 200"
#     payload = {
#         'channel': channel_id,
#         'text': '',
#         "attachments": [{
#             "color": status_colors.get(status),
#             "blocks": [
#                 {
#                     "type": "section",
#                     "text": {
#                         "type": "mrkdwn",
#                         "text": message
#                     }
#                 },
#                 {
#                     "type": "divider"
#                 },
#                 {
#                     "type": "actions",
#                     "elements": [
#                         {
#                             "type": "button",
#                             "text": {
#                                 "type": "plain_text",
#                                 "text": "Acknowledge",
#                                 "emoji": True
#                             }
#                         }
#                     ]
#                 },
#                 {
#                     "type": "context",
#                     "elements": [
#                         {
#                             "type": "mrkdwn",
#                             "text": "test context"
#                         }
#                     ]
#                 }
#             ]
#         }]
#     }
#     response = requests.post(
#         f'{url}/api/chat.postMessage',
#         headers=headers,
#         data=json.dumps(payload)
#     )
#     return response.json().get('ts')
def update_thread(channel_id, ts, status, message, chain_enabled=True, status_enabled=True):
    payload = {
        'channel': channel_id,
        'text': '',
        'attachments': [
            {
                'color': status_colors.get(status),
                'text': message,
                'mrkdwn_in': ['text'],
            },
            {
                'color': status_colors.get(status),
                'text': f'',
                "callback_id": "buttons",
                "actions": [
                    {
                        "name": 'chain',
                        "text": buttons['chain']['enabled']['text'] if chain_enabled else buttons['chain']['disabled']['text'],
                        "type": 'button',
                        "style": buttons['chain']['enabled']['style'] if chain_enabled else buttons['chain']['disabled']['style']
                    },
                    {
                        "name": 'status',
                        "text": buttons['status']['enabled']['text'] if status_enabled else buttons['status']['disabled']['text'],
                        "type": 'button',
                        "style": buttons['status']['enabled']['style'] if status_enabled else buttons['status']['disabled']['style'],
                    }
                ],
            },
        ],
        'ts': ts,
    }
    requests.post(
        f'{url}/api/chat.update',
        headers=headers,
        data=json.dumps(payload)
    )


def post_thread(channel_id, ts, text):
    payload = {
        'channel': channel_id,
        'text': text,
        'thread_ts': ts
    }
    r = requests.post(
        f'{url}/api/chat.postMessage',
        headers=headers,
        data=json.dumps(payload)
    )
    return r.status_code
