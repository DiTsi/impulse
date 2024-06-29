import json
from time import sleep

import requests

from app.logger import logger
from app.slack.user import User, UserGroup
from config import slack_bot_user_oauth_token

status_colors = {
    'firing': '#f61f1f',
    'unknown': '#c1a300',
    'resolved': '#56c15e',
    'closed': '#969696',
}
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {slack_bot_user_oauth_token}',
}
url = 'https://slack.com'
buttons = {
    'chain': {
        'enabled': {
            'text': '◼ Chain',
            'style': 'primary'
        },
        'disabled': {
            'text': '▶ Chain',
            'style': 'normal'  # danger
        }
    },
    'status': {
        'enabled': {
            'text': '◼ Status',
            'style': 'primary'
        },
        'disabled': {
            'text': '▶ Status',
            'style': 'normal'  # danger
        }
    }
}


def get_public_channels():
    try:
        response = requests.get(
            f'{url}/api/conversations.list',
            headers=headers
        )
        sleep(1.5)
        data = response.json()
        channels_list = data.get('channels', [])
        channels_dict = {c.get('name'): c for c in channels_list}
        return channels_dict
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to retrieve channel list: {e}')  # !
        return []


def admin_message(channel_id, message):
    payload = {
        'channel': channel_id,
        'text': message,
        'unfurl_links': False,
        'unfurl_media': False
    }
    response = requests.post(f'{url}/api/chat.postMessage', headers=headers, data=json.dumps(payload))
    return response.json().get('ts')


def create_thread(channel_id, message, status):
    payload = {
        'channel': channel_id,
        'text': '',
        'attachments': [
            {
                'color': status_colors.get(status),
                'text': message
            },
            {
                'color': status_colors.get(status),
                'text': '',
                "callback_id": "buttons",
                "actions": [
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


def button_handler(original_message, chain_enabled, status_enabled):
    if chain_enabled:
        original_message['attachments'][1]['actions'][0]['text'] = buttons['chain']['enabled']['text']
        original_message['attachments'][1]['actions'][0]['style'] = buttons['chain']['enabled']['style']
    else:
        original_message['attachments'][1]['actions'][0]['text'] = buttons['chain']['disabled']['text']
        original_message['attachments'][1]['actions'][0]['style'] = buttons['chain']['disabled']['style']

    if status_enabled:
        original_message['attachments'][1]['actions'][1]['text'] = buttons['status']['enabled']['text']
        original_message['attachments'][1]['actions'][1]['style'] = buttons['status']['enabled']['style']
    else:
        original_message['attachments'][1]['actions'][1]['text'] = buttons['status']['disabled']['text']
        original_message['attachments'][1]['actions'][1]['style'] = buttons['status']['disabled']['style']
    return original_message


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
