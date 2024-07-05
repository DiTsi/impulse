import json

import requests

from app.logger import logger
from . import buttons
from .chain import generate_chains
from .channels import get_public_channels
from .config import url, status_colors, headers
from .message_template import generate_message_template
from .messages import send_message
from .threads import post_thread, app_update_thread
from .user import admins_template_string, env, generate_users, generate_user_groups


class SlackApplication:
    def __init__(self, app_config, channels_list, default_channel):
        # create channels
        logger.debug(f'get Slack channels using API')
        public_channels = get_public_channels()
        logger.debug(f'get channels IDs for channels in route')
        channels = dict()
        for ch in channels_list:
            try:
                channels[ch] = public_channels[ch]
            except KeyError:
                logger.warning(f'no public channel \'{ch}\' in Slack')

        # create chains
        chains = generate_chains(app_config.get('chains', dict()))

        # create users, user_groups
        logger.debug(f'get Slack users using API')
        users = generate_users(app_config.get('users'))
        user_groups = generate_user_groups(app_config.get('user_groups'), users)

        # create channels
        channels = dict()
        for ch in channels_list:
            try:
                channels[ch] = public_channels[ch]
            except KeyError:
                logger.warning(f'no public channel \'{ch}\' in Slack')

        # create message_template
        message_template_dict = app_config.get('message_template')
        message_template = generate_message_template(message_template_dict)

        admins_list = app_config['admin_users']
        self.default_channel_id = channels[default_channel]['id']
        self.admin_users = [users[admin] for admin in admins_list]
        self.users = users
        self.user_groups = user_groups
        self.chains = chains
        self.channels = channels
        self.message_template = message_template
        self.type = 'slack'
        self.url = url

    def notify(self, incident, type_, identifier):
        admins_ids = [a.id for a in self.admin_users]
        if type_ == 'user':
            unit = self.users[identifier]
            text = unit.mention_text(admins_ids)
            response_code = post_thread(incident.channel_id, incident.ts, text)
            return response_code
        elif type_ == 'user_group':
            unit = self.user_groups[identifier]
            text = unit.mention_text(admins_ids)
            response_code = post_thread(incident.channel_id, incident.ts, text)
            return response_code
        else:
            pass

    def update(self, uuid_, incident, incident_status, alert_state, updated_status, chain_enabled, status_enabled):
        text = self.message_template.form_message(alert_state)
        app_update_thread(incident.channel_id, incident.ts, incident_status, text, chain_enabled, status_enabled)
        if updated_status:
            logger.info(f'Incident \'{uuid_}\' updated with new status \'{incident_status}\'')
            # post to thread
            if status_enabled and incident_status != 'closed':
                text = f'status updated: *{incident_status}*'
                if incident_status == 'unknown':
                    admins_ids = [a.id for a in self.admin_users]
                    admins_text = env.from_string(admins_template_string).render(users=admins_ids)
                    text += f'\n>_{admins_text}_'
                post_thread(incident.channel_id, incident.ts, text)

    def new_version_notification(self, channel_id, new_tag):
        admins_ids = [a.id for a in self.admin_users]
        admins_text = env.from_string(admins_template_string).render(users=admins_ids)
        text = (f'New IMPulse version available: {new_tag}'
                f'\n>_see <CHANGELOG.md|https://github.com/DiTsi/impulse/blob/main/CHANGELOG.md>_'
                f'\n>_{admins_text}_')
        send_message(channel_id, text)

    def create_thread(self, channel_id, message, status):
        payload = {
            'channel': channel_id,
            'text': '',
            'attachments': [
                {
                    'color': status_colors.get(status),
                    'text': message,
                    'mrkdwn_in': ['text'],
                },
                {
                    'color': status_colors.get(status),
                    'text': '',
                    'callback_id': 'buttons',
                    'actions': [
                        {
                            "name": "chain",
                            "text": buttons['chain']['enabled']['text'],
                            "type": "button",
                            "style": buttons['chain']['enabled']['style']
                        },
                        {
                            "name": "status",
                            "text": buttons['status']['enabled']['text'],
                            "type": "button",
                            "style": buttons['status']['enabled']['style']
                        }
                    ]
                }
            ]
        }
        response = requests.post(f'{self.url}/api/chat.postMessage', headers=headers, data=json.dumps(payload))
        return response.json().get('ts')
