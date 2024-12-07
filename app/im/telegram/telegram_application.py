import json
from time import sleep

import requests
from flask import jsonify

from app.im.application import Application
from app.im.telegram.config import buttons
from app.im.telegram.user import User
from app.logging import logger
from config import telegram_bot_token, application


# Temporary Firing: 🔥, Unknown: ❗️, Resolved: ✅, Closed: 🏁
class TelegramApplication(Application):
    icon_map = { #!
        '5312241539987020022': '🔥',
        '5379748062124056162': '❗️',
        '5237699328843200968': '✅',
        '5408906741125490282': '🏁'
    }

    def __init__(self, app_config, channels, users):
        super().__init__(app_config, channels, users)

    def _initialize_specific_params(self):
        self.url += telegram_bot_token
        self.post_message_url = self.url + '/sendMessage'
        self.headers = {'Content-Type': 'application/json'}
        self.post_delay = 0.5
        self.thread_id_key = 'message_id'
        self._setup_webhook()

    def _get_url(self, app_config):
        return 'https://api.telegram.org/bot'

    def _get_public_url(self, app_config):
        return 'https://api.telegram.org/bot'

    def _get_team_name(self, app_config):
        return None

    def get_notification_destinations(self):
        return self.admin_users

    def format_text_bold(self, text):
        return f'<b>{text}</b>'

    def _format_text_link(self, text, url):
        return f'<a href={url}>{text}</a>'

    def format_text_italic(self, text):
        return f'<i>{text}</i>'

    def _format_tg_icon(self, icon):
        return f'{self.icon_map.get(icon)}'

    def get_admins_text(self): #!
        return ', '.join([f'@{a.username}' for a in self.admin_users])

    def send_message(self, channel_id, text, attachment):
        params = {
            'chat_id': channel_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        response = self.http.post(self.post_message_url, params=params)
        sleep(self.post_delay)
        return response.json().get('result', {}).get('message_id')

    def _send_create_thread(self, payload):
        response = self.http.post(self.post_message_url, headers=self.headers, data=json.dumps(payload))
        sleep(self.post_delay)
        response_json = response.json()
        return response_json.get('result', {}).get(self.thread_id_key)

    def buttons_handler(self, payload, incidents, queue_, route):
        if 'callback_query' not in payload:
            return jsonify({}), 200
        callback = payload['callback_query']
        message_id = callback['message']['message_id']
        post_id = callback['message']['message_thread_id']
        thread_id = f'{post_id}/{message_id}'
        incident_ = incidents.get_by_ts(ts=thread_id)
        if incident_ is None:
            self.http.post(
                f'{self.url}/answerCallbackQuery',
                data=json.dumps({'callback_query_id': callback['id']}),
                headers=self.headers
            )
            return jsonify({}), 200
        action = callback['data']
        if action in ['start_chain', 'stop_chain']:
            if action == 'stop_chain':
                incident_.chain_enabled = False
                queue_.delete_by_id(incident_.uuid, delete_steps=True, delete_status=False)
            else:
                incident_.chain_enabled = True
                queue_.append(incident_.uuid, incident_.chain)
        elif action in ['start_status', 'stop_status']:
            if action == 'stop_status':
                incident_.status_enabled = False
            else:
                incident_.status_enabled = True
        self.http.post(
            f'{self.url}/editMessageReplyMarkup',
            data=json.dumps({
                'chat_id': callback['message']['chat']['id'],
                'message_id': message_id,
                'reply_markup': {
                    'inline_keyboard': [
                        [
                            buttons['chain']['enabled'] if incident_.chain_enabled else buttons['chain']['disabled'],
                            buttons['status']['enabled'] if incident_.status_enabled else buttons['status']['disabled']
                        ]
                    ]
                }
            }),
            headers=self.headers
        )
        self.http.post(
            f'{self.url}/answerCallbackQuery',
            data=json.dumps({'callback_query_id': callback['id']}),
            headers=self.headers
        )
        incident_.dump()
        return jsonify({}), 200

    @staticmethod
    def handle_message_creation(incidents, message):
        incident_ = incidents.get_by_ts(message['forward_from_message_id'])
        if incident_ is None:
            return jsonify({}), 200
        with incident_.lock():
            incident_.set_thread_id(message['message_id'])
            incident_.dump()
        return jsonify({}), 200


    def _create_thread_payload(self, channel_id, body, header, status_icons, status):
        return {
            'chat_id': channel_id,
            'text': f'{self._format_tg_icon(status_icons)} {header}\n{body}',
            'parse_mode': 'HTML',
            'reply_markup': {
                'inline_keyboard': [
                    [
                        buttons['chain']['enabled'],
                        buttons['status']['enabled']
                    ]
                ]
            }
        }

    def post_thread(self, channel_id, incident_, text):
        payload = self._post_thread_payload(channel_id, incident_.get_thread_id(), text)
        response = requests.post(self.post_message_url, headers=self.headers, data=json.dumps(payload))
        sleep(self.post_delay)
        return response.status_code

    def _post_thread_payload(self, channel_id, id_, text):
        thread_channel_id = self.channels.get(channel_id)['thread_channel_id']
        return {
            'chat_id': thread_channel_id,
            'text': text,
            'reply_parameters': {
                'message_id': id_
            },
            'parse_mode': 'HTML'
        }

    def update_thread_payload(self, channel_id, id_, body, header, status_icons, status, chain_enabled,
                              status_enabled):
        return {
            'chat_id': channel_id,
            'message_id': id_,
            'text': f'{self._format_tg_icon(status_icons)} {header}\n{body}',
            'parse_mode': 'HTML',
            'reply_markup': {
                'inline_keyboard': [
                    [
                        buttons['chain']['enabled'] if chain_enabled else buttons['chain']['disabled'],
                        buttons['status']['enabled'] if status_enabled else buttons['status']['disabled']
                    ]
                ]
            }
        }

    def _update_thread(self, id_, payload):
        try:
            self.http.post(
                f'{self.url}/editMessageText',
                data=json.dumps(payload),
                headers=self.headers
            )
            sleep(self.post_delay)
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to update thread: {e}')

    def _markdown_links_to_native_format(self, text):
        return text

    def get_user_details(self, user_details):
        id_ = user_details.get('id') if user_details is not None else None
        exists = False
        if id_ is not None:
            response = self.http.get(f'{self.url}/getChat?chat_id={id_}', headers=self.headers)
            data = response.json()
            if response.status_code == 200 and data.get('ok'):
                exists = True
        return {'id': id_, 'exists': exists}

    def create_user(self, name, user_details):
        return User(
            name=name,
            id_=user_details.get('id'),
            exists=user_details.get('exists', False)
        )

    def _setup_webhook(self):
        try:
            self.http.post(
                f'{self.url}/setWebhook',
                params={'url': f"{application.get('impulse_address')}/app"},
                headers=self.headers
            )
            sleep(self.post_delay)
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to set webhook: {e}')
            raise e
