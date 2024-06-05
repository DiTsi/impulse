import json
from time import sleep

import requests

from app.logger import logger
from app.slack.user import User, UserGroup
from config import slack_bot_user_oauth_token, slack_verification_token

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


def get_public_channels():
    try:
        response = requests.get(
            f'{url}/api/conversations.list',
            headers=headers
        )
        sleep(1)
        data = response.json()
        channels_list = data.get('channels', [])
        channels_dict = {c.get('name'): c for c in channels_list}
        return channels_dict
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to retrieve channel list: {e}')  # !
        return []


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
                "callback_id": "acknowledge",
                "actions": [
                    {
                        "name": "acknowledge",
                        "text": "Acknowledge",
                        "type": "button"
                    }
                ]
            }
        ]
    }
    response = requests.post(f'{url}/api/chat.postMessage', headers=headers, data=json.dumps(payload))
    return response.json().get('ts')


def button_handler(payload):
    if payload.get('token') != slack_verification_token:
        logger.error(f'Unauthorized request to \'/slack\'')
        return {}, 401
    modified_message = payload.get('original_message')
    if modified_message['attachments'][1]['actions'][0]['text'] == 'Acknowledge':
        modified_message['attachments'][1]['actions'][0]['text'] = 'Unacknowledge'
        modified_message['attachments'].append({
            'color': modified_message['attachments'][1].get('color'),
            'text': f"Acknowledged by <@{payload['user']['id']}>"
        })
    else:
        modified_message['attachments'][1]['actions'][0]['text'] = 'Acknowledge'
        del modified_message['attachments'][2]
    return modified_message


def create_blocked_thread(channel_id, message, status): #! didn't work with "return modified_message, 200"
    payload = {
        'channel': channel_id,
        'text': '',
        "attachments": [{
            "color": status_colors.get(status),
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Acknowledge",
                                "emoji": True
                            }
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "test context"
                        }
                    ]
                }
            ]
        }]
    }
    response = requests.post(
        f'{url}/api/chat.postMessage',
        headers=headers,
        data=json.dumps(payload)
    )
    return response.json().get('ts')


def update_thread(channel_id, ts, status, message, acknowledge=False, user_id=None):
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
                'text': f'Acknowledged by <@{user_id}>' if acknowledge else '',
                "callback_id": "acknowledge",
                "actions": [
                    {
                        "name": "unacknowledge" if acknowledge else 'acknowledge',
                        "text": "Unacknowledge" if acknowledge else 'Acknowledge',
                        "type": "button",
                        "style": "default",
                    },
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
