from time import sleep

import requests

from app.logger import logger
from config import slack_bot_user_oauth_token
from jinja2 import Environment

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {slack_bot_user_oauth_token}',
}
url = 'https://slack.com'


def bold_text(value):
    return f"*{value}*"


def slack_mention_text(value):
    return f"<@{value}>"


env = Environment()
env.filters['bold_text'] = bold_text
env.filters['slack_mention_text'] = slack_mention_text
users_template_string = "{{ users | map('bold_text') | join(', ') }}"
admins_template_string = "{{ users | map('slack_mention_text') | join(', ') }}"


class User:
    def __init__(self, name, slack_id=None):
        self.name = name
        self.slack_id = slack_id

    def __repr__(self):
        return self.name

    def mention_text(self, admins_ids):
        text = f'notify user *{self.name}*'
        if self.slack_id:
            text += f': <@{self.slack_id}>'
        else:
            admins_text = env.from_string(admins_template_string).render(users=admins_ids)
            text += (f'\n>_not found in Slack_'
                     f'\n>_{admins_text}_')
        return text


class UserGroup:
    def __init__(self, name, users):
        self.name = name
        self.users = users

    def mention_text(self, admins_ids):
        text = f'notify user_group *{self.name}*: '
        not_found_users = list()
        not_found = False
        for user in self.users:
            if user.slack_id:
                text += f'<@{user.slack_id}> '
            else:
                not_found = True
                not_found_users.append(user.name)
        if not_found:
            not_found_users_text = env.from_string(users_template_string).render(users=not_found_users)
            admins_text = env.from_string(admins_template_string).render(users=admins_ids)
            text += (f'\n>_users [{not_found_users_text}] not found in Slack_'
                     f'\n>_{admins_text}_')
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


def generate_users(users_dict=None):
    def get_user_id_(s_users, full_name):
        for u in s_users:
            if u.get('real_name') == full_name:
                return u['id']
        logger.warning(f'User \'{full_name}\' not found in Slack')
        return None

    users = dict()
    if users_dict:
        logger.debug(f'creating users')
        slack_users = get_users()
        for name in users_dict.keys():
            slack_fullname = users_dict[name]['full_name']
            slack_id = get_user_id_(slack_users, slack_fullname)
            users[name] = User(name, slack_id=slack_id)
        return users
    else:
        logger.debug(f'no users defined in impulse.yml')
        return users


def generate_user_groups(user_groups_dict=None, users=None):
    user_groups = dict()
    if user_groups_dict:
        logger.debug(f'creating user_groups')
        for name in user_groups_dict.keys():
            user_names = user_groups_dict[name]['users']
            user_objects = [users.get(user_name) for user_name in user_names]
            user_groups[name] = UserGroup(name, user_objects)
        logger.debug(f'user_groups created')
    else:
        logger.debug(f'No user_groups defined in impulse.yml. Continue with empty user_groups')
    return user_groups
