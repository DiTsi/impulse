import json
from time import sleep

import requests

from app.im.application import Application
from app.im.telegram.threads import telegram_get_create_thread_payload
from app.im.telegram.user import User
from app.logging import logger
from config import tg_bot_token, impulse_url


class TelegramApplication(Application):
    def __init__(self, app_config, channels, users):
        super().__init__(app_config, channels, users)

    def _initialize_specific_params(self):
        self.url += tg_bot_token
        self.post_message_url = self.url + '/sendMessage'
        self.headers = None
        self.post_delay = 0.5
        self.thread_id_key = 'message_id'
        self._setup_webhook()

    def get_channels(self, channels_list):
        channels = {}
        for channel_id in channels_list:
            try:
                response = self.http.get(
                    f'{self.url}/getChat',
                    params={'chat_id': channel_id},
                )
                response.raise_for_status()
                sleep(self.post_delay)
                channel_info = response.json().get('result')
                channels[channel_info.get('id')] = {
                    'id': channel_info.get('id'),
                    'linked_chat_id': channel_info.get('linked_chat_id')
                }
            except requests.exceptions.RequestException as e:
                logger.error(f'Failed to retrieve public channels list: {e}')
        return channels

    def _get_public_channels(self):
        """ Not needed for Telegram """
        pass

    def _get_private_channels(self):
        """ Not needed for Telegram """
        pass

    def _get_url(self, app_config):
        return app_config['url']

    def _get_team_name(self, app_config):
        return None

    def get_notification_destinations(self):
        return [a.username for a in self.admin_users]

    def format_text_bold(self, text):
        return f'*{text}*'

    def _format_text_link(self, text, url):
        return f'[{text}]({url})'

    def _format_text_italic(self, text):
        return f'_{text}_'

    def _format_text_citation(self, text):
        return f'>{text}'

    def get_admins_text(self):
        return ', '.join([a.username for a in self.admin_users])

    def send_message(self, channel_id, text, attachment):
        params = {
            'chat_id': channel_id,
            'text': text,
            'parse_mode': 'MarkdownV2'
        }
        response = self.http.post(self.post_message_url, params=params)
        sleep(self.post_delay)
        return response.json().get('message_id')

    def _create_thread_payload(self, channel_id, body, header, status_icons, status):
        return telegram_get_create_thread_payload(channel_id, body, header, status_icons, status)

    def _post_thread_payload(self, channel_id, id_, text):
        channel = self.channels[channel_id]
        return {
            'chat_id': channel_id,
            'text': text,
            'reply_to_message_id': id_,
            'parse_mode': 'MarkdownV2'
        }

    def _update_thread_payload(self, channel_id, id_, body, header, status_icons, status, chain_enabled,
                               status_enabled):
        return {
            'chat_id': channel_id,
            'message_id': id_,
            'text': f'{status_icons} {status} {header}\n{body}',
            'parse_mode': 'MarkdownV2'
        }

    def _update_thread(self, id_, payload):
        try:
            self.http.post(
                f'{self.url}/editMessageText',
                data=json.dumps(payload)
            )
            sleep(self.post_delay)
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to update thread: {e}')

    def _get_users(self, users):
        return users

    def get_user_details(self, s_users, user_info):
        return {
            'username': user_info['username'],
            'name': user_info.get('name')
        }

    def create_user(self, name, user_details):
        return User(
            name=name,
            username=user_details['username']
        )

    def _setup_webhook(self):
        try:
            self.http.post(
                f'{self.url}/setWebhook',
                params={'url': f'{impulse_url}/app'}
            )
            sleep(self.post_delay)
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to set webhook: {e}')
            raise e