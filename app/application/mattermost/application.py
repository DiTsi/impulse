import json
from time import sleep

import requests

from app.logger import logger
from . import buttons
from .chain import generate_chains
from .channels import get_public_channels
from .config import headers, status_colors
from .me import get_me
from .message_template import generate_message_template
from .messages import send_message
from .teams import get_team
from .threads import update_thread
from .user import admins_template_string, env, generate_users, generate_user_groups


class MattermostApplication:
    def __init__(self, app_config, channels_list, default_channel):
        url = app_config['url']
        # get teams
        team_name = app_config['team']
        team = get_team(url, team_name)
        # create channels
        logger.debug(f'get Mattermost channels using API')
        public_channels = get_public_channels(url, team)
        logger.debug(f'get channels IDs for channels in route')
        channels = dict()
        for ch in channels_list:
            try:
                channels[ch] = public_channels[ch]
            except KeyError:
                logger.warning(f'no public channel \'{ch}\' in Mattermost')

        # create chains
        chains = generate_chains(app_config.get('chains', dict()))

        me = get_me(url)

        # create users, user_groups
        logger.debug(f'get Mattermost users using API')
        users = generate_users(url, team['id'], app_config.get('users'))
        user_groups = generate_user_groups(app_config.get('user_groups'), users)

        # create channels
        channels = dict()
        for ch in channels_list:
            try:
                channels[ch] = public_channels[ch]
            except KeyError:
                logger.warning(f'no public channel \'{ch}\' in Mattermost')

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
        self.type = 'mattermost'
        self.url = url

    def notify(self, incident, type_, identifier):
        admins_ids = [a.id for a in self.admin_users]
        if type_ == 'user':
            unit = self.users[identifier]
            text = unit.mention_text(admins_ids)
            response_code = self.post_thread(incident.channel_id, incident.ts, text)
            return response_code
        elif type_ == 'user_group':
            unit = self.user_groups[identifier]
            text = unit.mention_text(admins_ids)
            response_code = self.post_thread(incident.channel_id, incident.ts, text)
            return response_code
        else:
            pass

    def update(self, uuid_, incident, incident_status, alert_state, updated_status, chain_enabled, status_enabled):
        text = self.message_template.form_message(alert_state)
        update_thread(incident.channel_id, incident.ts, incident_status, text, chain_enabled, status_enabled)
        if updated_status:
            logger.info(f'Incident \'{uuid_}\' updated with new status \'{incident_status}\'')
            # post to thread
            if status_enabled and incident_status != 'closed':
                text = f'status updated: *{incident_status}*'
                if incident_status == 'unknown':
                    admins_ids = [a.id for a in self.admin_users]
                    admins_text = env.from_string(admins_template_string).render(users=admins_ids)
                    text += f'\n>_{admins_text}_'
                self.post_thread(incident.channel_id, incident.ts, text)

    def new_version_notification(self, channel_id, new_tag):
        admins_ids = [a.id for a in self.admin_users]
        admins_text = env.from_string(admins_template_string).render(users=admins_ids)
        text = (f'New IMPulse version available: {new_tag}'
                f'\n>_see <CHANGELOG.md|https://github.com/DiTsi/impulse/blob/main/CHANGELOG.md>_'
                f'\n>_{admins_text}_')
        send_message(channel_id, text)

    def create_thread(self, channel_id, message, status):
        payload = {
            'channel_id': channel_id,
            'message': message,
            'props': {
                'attachments': [
                    {
                        'fallback': 'test',
                        'text': '',
                        'color': status_colors.get(status),
                        'actions': [
                            {
                                "id": "chain",
                                "type": "button",
                                "name": buttons['chain']['enabled']['text'],
                                "style": "good", # good, warning, danger, default, primary, and success
                                "integration": {
                                    "url": "http://127.0.0.1:7357",
                                    "context": {
                                        "action": "chain"
                                    }
                                }
                            },
                            {
                                "id": "status",
                                "type": "button",
                                "name": buttons['status']['enabled']['text'],
                                "style": "good", # good, warning, danger, default, primary, and success
                                "integration": {
                                    "url": "http://127.0.0.1:7357",
                                    "context": {
                                        "action": "status"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
        response = requests.post(f'{self.url}/api/v4/posts', headers=headers, data=json.dumps(payload))
        sleep(0.1)
        return response.json().get('create_at')

    def post_thread(self, channel_id, ts, text):
        payload = {
            'channel': channel_id,
            'message': text,
            # 'thread_ts': ts
        }
        r = requests.post(
            f'{self.url}/api/v4/posts',
            headers=headers,
            data=json.dumps(payload)
        )
        sleep(0.1)
        return r.status_code
