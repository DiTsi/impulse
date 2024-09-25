from time import sleep

import requests

from app.im.slack.config import slack_headers, slack_bold_text, slack_mention_text, slack_env, \
    slack_admins_template_string, slack_request_delay
from app.logging import logger


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
            text += (f'not found in Slack\n'
                     f'➤ admins: {admins_text}')
        return text
