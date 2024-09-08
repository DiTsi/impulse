import json
from time import sleep

import requests

from app.im.application import Application
from app.im.mattermost import mattermost_get_public_channels, mattermost_send_message
from app.im.mattermost.config import (mattermost_headers, mattermost_request_delay, mattermost_bold_text,
                                      mattermost_env, mattermost_admins_template_string)
from app.im.mattermost.teams import get_team
from app.im.mattermost.threads import mattermost_get_create_thread_payload, mattermost_get_update_payload
from app.im.mattermost.user import mattermost_generate_users


class MattermostApplication(Application):
    def __init__(self, app_config, channels_list, default_channel):
        super().__init__(app_config, channels_list, default_channel)

        self.post_message_url = f'{self.url}/api/v4/posts'
        self.headers = mattermost_headers
        self.post_delay = mattermost_request_delay
        self.thread_id_key = 'id'

    def _get_public_channels(self):
        team = get_team(self.url, self.team)
        return mattermost_get_public_channels(self.url, team)

    def _get_url(self, app_config):
        return app_config['url']

    def _get_team_name(self, app_config):
        return app_config['team']

    def _generate_users(self, users_dict):
        return mattermost_generate_users(self.url, users_dict)

    def get_notification_destinations(self):
        return [a.username for a in self.admin_users]

    def format_text_bold(self, text):
        return mattermost_bold_text(text)

    def _format_text_italic(self, text):
        return f'_{text}_'

    def _format_text_citation(self, text):
        return f'_{text}_'

    def _format_text_link(self, text, url):
        return f"([{text}]({url}))"

    def get_admins_text(self):
        admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(
            users=self.get_notification_destinations()
        )
        return admins_text

    def send_message(self, channel_id, text, attachment):
        mattermost_send_message(self.url, channel_id, text, attachment)

    def _create_thread_payload(self, channel_id, body, header, status_icons, status):
        return mattermost_get_create_thread_payload(channel_id, body, header, status_icons, status)

    def _post_thread_payload(self, channel_id, id_, text):
        return {'channel_id': channel_id, 'root_id': id_, 'message': text}

    def _update_thread_payload(self, channel_id, id_, body, header, status_icons, status, chain_enabled,
                               status_enabled):
        return mattermost_get_update_payload(channel_id, id_, body, header, status_icons, status, chain_enabled,
                                             status_enabled)

    def _update_thread(self, id_, payload):
        requests.put(
            f'{self.url}/api/v4/posts/{id_}',
            headers=mattermost_headers,
            data=json.dumps(payload)
        )
        sleep(self.post_delay)
