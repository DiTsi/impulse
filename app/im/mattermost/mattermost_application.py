import json
from time import sleep

import requests

from app.im.application import Application
from app.im.colors import status_colors
from app.im.exceptions import UserGenerationError
from app.im.mattermost.config import (mattermost_headers, mattermost_request_delay, mattermost_bold_text,
                                      mattermost_env, mattermost_admins_template_string)
from app.im.mattermost.teams import get_team
from app.im.mattermost.threads import mattermost_get_create_thread_payload, mattermost_get_update_payload
from app.im.mattermost.user import User
from app.logging import logger


class MattermostApplication(Application):

    def __init__(self, app_config, channels_list, default_channel):
        super().__init__(app_config, channels_list, default_channel)

    def _initialize_specific_params(self):
        self.post_message_url = f'{self.url}/api/v4/posts'
        self.headers = mattermost_headers
        self.post_delay = mattermost_request_delay
        self.thread_id_key = 'id'

    def _get_public_channels(self) -> dict:
        team = get_team(self.url, self.team)
        if not team:
            return {}
        return self._get_channels(team)

    def _get_private_channels(self) -> dict:
        try:
            response = self.http.get(
                f"{self.url}/api/v4/channels",
                params={'per_page': 1000},
                headers=self.headers
            )
            response.raise_for_status()
            sleep(self.post_delay)
            data = response.json()
            return {c.get('name'): c for c in data}
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to retrieve channel list: {e}')
            return {}

    def _get_channels(self, team):
        try:
            response = self.http.get(
                f"{self.url}/api/v4/teams/{team['id']}/channels",
                params={'per_page': 1000},
                headers=self.headers
            )
            response.raise_for_status()
            sleep(self.post_delay)
            data = response.json()
            return {c.get('name'): c for c in data}
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to retrieve channel list: {e}')
            return {}

    def _get_team(self):
        try:
            response = self.http.get(
                f'{self.url}/api/v4/teams',
                params={'per_page': 200},
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return next((team for team in data if team['display_name'] == self.team), None)
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to retrieve teams list: {e}')
            return None

    def _get_url(self, app_config):
        return app_config['url']

    def _get_team_name(self, app_config):
        logger.info(f'Get {self.type.capitalize()} team name')
        return app_config['team']

    def get_user_details(self, s_users, user_info):
        username = user_info['username']
        user = next((u for u in s_users if u.get('username') == username), None)
        if user:
            return {
                'username': username,
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name')
            }
        logger.warning(f"User '{username}' not found in Mattermost")
        return {'username': username, 'first_name': None, 'last_name': None}

    def _get_users(self, users):
        usernames = [u['username'] for k, u in users.items()]
        logger.info(f'Get users from Mattermost')
        try:
            response = self.http.post(
                f'{self.url}/api/v4/users/usernames',
                data=json.dumps(usernames),
                headers=self.headers
            )
            response.raise_for_status()
            sleep(self.post_delay)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'Incorrect Mattermost response. Reason: {e}')
            raise UserGenerationError(f'Failed to retrieve users: {e}')

    def create_user(self, name, user_details):
        return User(
            name=name,
            username=user_details['username'],
            first_name=user_details.get('first_name', ''),
            last_name=user_details.get('last_name', '')
        )

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
        payload = {
            'channel_id': channel_id,
            'message': text,
            'props': {
                'attachments': [
                    {
                        'fallback': 'test',
                        'text': attachment,
                        'color': status_colors['closed']
                    }
                ]
            }
        }
        response = self.http.post(f'{self.url}/api/v4/posts', headers=self.headers, data=json.dumps(payload))
        sleep(self.post_delay)
        return response.json().get('ts')

    def _create_thread_payload(self, channel_id, body, header, status_icons, status):
        return mattermost_get_create_thread_payload(channel_id, body, header, status_icons, status)

    def _post_thread_payload(self, channel_id, id_, text):
        return {'channel_id': channel_id, 'root_id': id_, 'message': text}

    def _update_thread_payload(self, channel_id, id_, body, header, status_icons, status, chain_enabled,
                               status_enabled):
        return mattermost_get_update_payload(channel_id, id_, body, header, status_icons, status, chain_enabled,
                                             status_enabled)

    def _update_thread(self, id_, payload):
        self.http.put(
            f'{self.url}/api/v4/posts/{id_}',
            headers=mattermost_headers,
            data=json.dumps(payload)
        )
        sleep(self.post_delay)

    def _markdown_links_to_native_format(self, text):
        return text
