from time import sleep

import requests

from app.logging import logger
from .config import slack_headers, slack_bold_text, slack_mention_text, slack_env, slack_admins_template_string, \
    slack_request_delay


class User:
    def __init__(self, name, slack_id=None):
        self.name = name
        self.slack_id = slack_id

    def __repr__(self):
        return self.name

    def mention_text(self, admins_ids):
        text = f'➤ user {slack_bold_text(self.name)}: '
        if self.slack_id:
            text += f'{slack_mention_text(self.slack_id)}'
        else:
            admins_text = slack_env.from_string(slack_admins_template_string).render(users=admins_ids)
            text += (f'*not found in Slack*\n'
                     f'➤ admins: {admins_text}')
        return text


def slack_get_users(url):
    response = requests.get(
        f'{url}/api/users.list',
        headers=slack_headers
    )
    sleep(slack_request_delay)
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
        logger.debug(f'Creating users')
        slack_users = slack_get_users(url)
        for name in users_dict.keys():
            slack_fullname = users_dict[name]['full_name']
            slack_id = get_user_id_(slack_users, slack_fullname)
            users[name] = User(name, slack_id=slack_id)
        return users
    else:
        logger.debug(f'No users defined in impulse.yml')
        return users
