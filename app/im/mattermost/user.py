from time import sleep

import requests

from app.im.mattermost.config import (mattermost_headers, mattermost_bold_text, mattermost_mention_text, mattermost_env,
                                      mattermost_admins_template_string, mattermost_request_delay)
from app.logging import logger


class User:
    def __init__(self, username, first_name, last_name):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    def __repr__(self):
        return self.username

    def mention_text(self, admins_usernames):
        if self.first_name is not None:
            if self.first_name == '' and self.last_name == '':
                fullname = self.username
            else:
                fullname = self.first_name + ' ' + self.last_name
            text = f'➤ user {mattermost_bold_text(fullname)}: '
            text += f'{mattermost_mention_text(self.username)}'
        else:
            text = f'➤ user {mattermost_bold_text(self.username)}: '
            admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(users=admins_usernames)
            text += (f'**not found in Mattermost**\n'
                     f'➤ admins: {admins_text}')
        return text


def mattermost_get_users(url):
    response = requests.get(
        f'{url}/api/v4/users',
        headers=mattermost_headers
    )
    sleep(mattermost_request_delay)
    if not response.ok:
        logger.error(f'Incorrect Mattermost response. Reason: {response.reason}')
        exit()
    json_ = response.json()
    return json_


def mattermost_generate_users(url, users_dict=None):
    def get_first_and_last_names(s_users, username):
        for u in s_users:
            if u.get('username') == username:
                return u['first_name'], u['last_name']
        logger.warning(f'User \'{username}\' not found in Mattermost')
        return None, None

    users = dict()
    if users_dict:
        logger.debug(f'Creating users')
        mattermost_users = mattermost_get_users(url)
        for name in users_dict.keys():
            mattermost_fullname = users_dict[name]['username']
            first_name, last_name = get_first_and_last_names(mattermost_users, mattermost_fullname)
            users[name] = User(name, first_name, last_name)
        return users
    else:
        logger.debug(f'no users defined in impulse.yml')
        return users
