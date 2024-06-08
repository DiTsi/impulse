from time import sleep

import requests

from app.logger import logger
from config import debug_slack_mention, slack_bot_user_oauth_token

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
        text = f'notify user *{self.name}*'
        if debug_slack_mention == 'False':
            text += f': <@{self.slack_id}>'
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
        text = f'notify user_group *{self.name}*'
        if debug_slack_mention == 'False':
            text += f': '
            for user in self.users:
                text += f'<@{user.slack_id}> '
        return text


class AdminGroup:
    def __init__(self, users):
        self.users = users

    def unknown_status_text(self):
        text = f'>notify admin_users: '
        if debug_slack_mention == 'False':
            for user in self.users:
                text += f'<@{user.slack_id}> '
        else:
            for user in self.users:
                text += f'{user.name} '
        text += (
            f'\n>_Check Alertmanager\'s `repeat_interval` option is less than IMPulse option `firing_timeout`_'
        ) #! add link to documentation
        return text


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


def generate_users(users_dict, slack_users):
    def get_user_id_(s_users, user):
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
