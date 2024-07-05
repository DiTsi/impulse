from time import sleep

import requests

from app.logging import logger
from .config import slack_headers
from jinja2 import Environment


def slack_bold_text(value):
    return f"*{value}*"


def slack_mention_text(value):
    return f"<@{value}>"


slack_env = Environment()
slack_env.filters['slack_bold_text'] = slack_bold_text
slack_env.filters['slack_mention_text'] = slack_mention_text
slack_users_template_string = "{{ users | map('slack_bold_text') | join(', ') }}"
slack_admins_template_string = "{{ users | map('slack_mention_text') | join(', ') }}"


class User:
    def __init__(self, name, slack_id=None):
        self.name = name
        self.slack_id = slack_id

    def __repr__(self):
        return self.name

    def mention_text(self, admins_ids):
        text = f'notify user {slack_bold_text(self.name)}'
        if self.slack_id:
            text += f': {slack_mention_text(self.slack_id)}'
        else:
            admins_text = slack_env.from_string(slack_admins_template_string).render(users=admins_ids)
            text += (f'\n>_not found in Slack_'
                     f'\n>_{admins_text}_')
        return text


def slack_get_users(url):
    response = requests.get(
        f'{url}/api/users.list',
        headers=slack_headers
    )
    sleep(1)
    if not response.ok:
        logger.error(f'Incorrect Slack response. Reason: {response.reason}')
        exit()
    json_ = response.json()
    return json_['members']


def slack_generate_users(url, users_dict=None):
    def get_user_id_(s_users, full_name):
        for u in s_users:
            if u.get('real_name') == full_name:
                return u['id']
        logger.warning(f'User \'{full_name}\' not found in Slack')
        return None

    users = dict()
    if users_dict:
        logger.debug(f'creating users')
        slack_users = slack_get_users(url)
        for name in users_dict.keys():
            slack_fullname = users_dict[name]['full_name']
            slack_id = get_user_id_(slack_users, slack_fullname)
            users[name] = User(name, slack_id=slack_id)
        return users
    else:
        logger.debug(f'no users defined in impulse.yml')
        return users
