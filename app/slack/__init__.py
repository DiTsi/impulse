import json
from time import sleep

import requests

from app.logger import logger
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


class User:
    def __init__(self, name, slack_id=None):
        self.name = name
        self.slack_id = slack_id

    def __repr__(self):
        return self.name

    def mention_text(self):
        text = f'user *{self.name}*: <@{self.slack_id}>'
        return text


class UserGroup:
    def __init__(self, name, users):
        self.name = name
        self.users = users

    # def get_actions(self, action):
    #     if action == 'webhook':
    #         return [u.webhook for u in self.users]
    #     elif action == 'mention':
    #         return [u.slack_mention for u in self.users]

    def mention_text(self):
        text = f'user_group *{self.name}*: '
        for user in self.users:
            text += f'<@{user.slack_id}> '
        return text


class AdminGroup:
    def __init__(self, users):
        self.users = users

    def unknown_status_text(self):
        text = (f'admin_users: ')
        for user in self.users:
            text += f'<@{user.slack_id}> '
        text += (
            f'\n>status changed to *unknown*'
            f'\n>Check Alertmanager\'s `repeat_interval` option is less than IMPulse option `firing_timeout`'
        ) #! add link to documentation
        return text


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


def get_users():
    response = requests.post(
        f'{url}/api/users.list',
        headers=headers
    )
    sleep(1)
    if not response.ok:
        logger.error(f'Incorrect Slack response. Reason: {response.reason}')
        exit()
    json_ = response.json()
    return json_['members']


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
                        "style": "default" if acknowledge else 'danger',
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


def generate_users(users_dict, slack_users):
    def get_user_id_(s_users, user):
        if user is None:
            return None
        for u in s_users:
            if u.get('real_name') == user:
                return u['id']
        logger.warning(f'User \'{user}\' not found in Slack')
        return None

    logger.debug(f'creating users')
    users = {}
    for name in users_dict.keys():
        slack_name = users_dict[name]['full_name']
        slack_id = get_user_id_(slack_users, slack_name)
        users[name] = User(name, slack_id=slack_id)
    return users


def generate_user_groups(user_groups_dict, users):
    logger.debug(f'creating user_groups')
    user_groups = {}
    for name in user_groups_dict.keys():
        user_names = user_groups_dict[name]['users']
        user_objects = [users.get(user_name) for user_name in user_names]
        user_groups[name] = UserGroup(name, user_objects)
    logger.debug(f'user_groups created')
    return user_groups


def generate_admin_group(admin_users, users):
    logger.debug(f'creating admin_users') #!
    user_objects = []
    for admin in admin_users:
        user_objects.append(users.get(admin))
    logger.debug(f'admin_users created') #!
    return AdminGroup(user_objects)
