import json

import requests

from app.im.application import Application
from app.im.slack import slack_get_public_channels, slack_send_message
from app.im.slack.config import slack_headers, slack_request_delay, slack_bold_text, slack_env, \
    slack_admins_template_string
from app.im.slack.threads import slack_get_create_thread_payload, slack_get_update_payload
from app.im.slack.user import slack_generate_users


class SlackApplication(Application):
    def __init__(self, app_config, channels_list, default_channel):
        super().__init__(app_config, channels_list, default_channel)

        self.post_message_url = f'{self.url}/api/chat.postMessage'
        self.headers = slack_headers
        self.post_delay = slack_request_delay
        self.thread_id_key = 'ts'

    def _get_public_channels(self):
        return slack_get_public_channels(self.url)

    def _get_url(self, app_config):
        return 'https://slack.com'

    def _get_team_name(self, app_config):
        return None

    def _generate_users(self, users_dict):
        return slack_generate_users(self.url, users_dict)

    def get_notification_destinations(self):
        return [a.slack_id for a in self.admin_users]

    def format_text_bold(self, text):
        return slack_bold_text(text)

    def _format_text_italic(self, text):
        return f'_{text}_'

    def _format_text_citation(self, text):
        return f'{text}'

    def _format_text_link(self, text, url):
        return f"(<{url}|{text}>)"

    def get_admins_text(self):
        admins_text = slack_env.from_string(slack_admins_template_string).render(
            users=self.get_notification_destinations()
        )
        return admins_text

    def send_message(self, channel_id, text, attachment):
        slack_send_message(self.url, channel_id, text, attachment)

    def _create_thread_payload(self, channel_id, body, header, status_icons, status):
        return slack_get_create_thread_payload(channel_id, body, header, status_icons, status)

    def _post_thread_payload(self, channel_id, id, text):
        return {'channel': channel_id, 'thread_ts': id, 'text': text}

    def _update_thread_payload(self, channel_id, id_, body, header, status_icons, status, chain_enabled,
                               status_enabled):
        return slack_get_update_payload(channel_id, id_, body, header, status_icons, status, chain_enabled,
                                        status_enabled)

    def _update_thread(self, id_, payload):
        requests.post(
            f'{self.url}/api/chat.update',
            headers=slack_headers,
            data=json.dumps(payload)
        )
