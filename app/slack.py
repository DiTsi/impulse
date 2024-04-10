import json

import requests

from config import slack_bot_user_oauth_token

headers = {
    'Content-Type': 'application/json',  #! 'missing_charset'
    'Authorization': f'Bearer {slack_bot_user_oauth_token}',
}
status_colors = {
    'firing': '#f61f1f',
    'unknown': '#c1a300',
    'resolved': '#56c15e',
    'closed': '#969696',
}


def create_thread(channel_id, message, status):
    url = 'https://slack.com/api/chat.postMessage'
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
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json().get('ts')


def create_blocked_thread(channel_id, message, status): #! didn't work with "return modified_message, 200"
    url = 'https://slack.com/api/chat.postMessage'
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
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json().get('ts')


def update_thread(channel_id, ts, status, message, acknowledge=False, user_id=None):
    url = 'https://slack.com/api/chat.update'
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
                        "style": "default" if acknowledge else 'danger',
                    },
                ],
            },
        ],
        'ts': ts,
    }
    requests.post(url, headers=headers, data=json.dumps(payload))


def get_public_channels():
    url = 'https://slack.com/api/conversations.list'
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        channels_list = data.get('channels', [])
        channels_dict = {c.get('name'): c for c in channels_list}
        return channels_dict
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve channel list: {e}') #!
        return []
