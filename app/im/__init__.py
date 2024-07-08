import json
from time import sleep

import requests

from app.logging import logger
from .chain import generate_chains
from .groups import generate_user_groups
from .mattermost import mattermost_send_message
from .mattermost.channels import mattermost_get_public_channels
from .mattermost.config import mattermost_headers, mattermost_bold_text, mattermost_admins_template_string, \
    mattermost_env
from .mattermost.teams import get_team
from .mattermost.threads import mattermost_get_create_thread_payload
from .mattermost.threads import mattermost_get_update_payload
from .mattermost.user import mattermost_generate_users
from .message_template import generate_message_template
from .slack import slack_send_message
from .slack.buttons import slack_buttons_handler
from .mattermost.buttons import mattermost_buttons_handler
from .slack.channels import slack_get_public_channels
from .slack.config import slack_headers, slack_bold_text, slack_admins_template_string, slack_env
from .slack.threads import slack_get_create_thread_payload
from .slack.threads import slack_get_update_payload
from .slack.user import slack_generate_users


class Application:
    def __init__(self, app_config, channels_list, default_channel):
        type = app_config['type']
        if type == 'slack':
            url = 'https://slack.com'
            logger.debug(f'get {type.capitalize()} channels using API')
            public_channels = slack_get_public_channels(url)
            team_name = None
        else:
            url = app_config['url']
            team_name = app_config['team']
            team = get_team(url, team_name)
            logger.debug(f'get {type.capitalize()} channels using API')
            public_channels = mattermost_get_public_channels(url, team)

        logger.debug(f'get channels IDs for channels in route')
        channels = dict()
        for ch in channels_list:
            try:
                channels[ch] = public_channels[ch]
            except KeyError:
                logger.warning(f'no public channel \'{ch}\' in {type.capitalize()}')

        chains = generate_chains(app_config.get('chains', dict()))
        logger.debug(f'get {type.capitalize()} users using API')
        if type == 'slack':
            users = slack_generate_users(url, app_config.get('users'))
        else:
            users = mattermost_generate_users(url, app_config.get('users'))
        user_groups = generate_user_groups(app_config.get('user_groups'), users)

        channels = dict()
        for ch in channels_list:
            try:
                channels[ch] = public_channels[ch]
            except KeyError:
                logger.warning(f'no public channel \'{ch}\' in {type.capitalize()}')

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
        self.team = team_name
        self.type = type
        self.url = url

    def notify(self, incident, notify_type, identifier):
        if self.type == 'slack':
            admins_ids = [a.id for a in self.admin_users]
            if notify_type == 'user':
                unit = self.users[identifier]
                text = unit.mention_text(admins_ids)
                response_code = self.post_thread(incident.channel_id, incident.ts, text)
                return response_code
            else:
                unit = self.user_groups[identifier]
                text = unit.mention_text(self.type, admins_ids)
                response_code = self.post_thread(incident.channel_id, incident.ts, text)
                return response_code
        else:
            admins_names = [a.username for a in self.admin_users]
            if notify_type == 'user':
                unit = self.users[identifier]
                text = unit.mention_text(admins_names)
                response_code = self.post_thread(incident.channel_id, incident.ts, text)
                return response_code
            else:
                unit = self.user_groups[identifier]
                text = unit.mention_text(self.type, admins_names)
                response_code = self.post_thread(incident.channel_id, incident.ts, text)
                return response_code

    def update(self, uuid_, incident, incident_status, alert_state, updated_status, chain_enabled, status_enabled):
        text = self.message_template.form_message(alert_state)
        self.update_thread(incident.channel_id, incident.ts, incident_status, text, chain_enabled, status_enabled)
        if updated_status:
            logger.info(f'Incident \'{uuid_}\' updated with new status \'{incident_status}\'')
            # post to thread
            if status_enabled and incident_status != 'closed':
                if self.type == 'slack':
                    text = f'status updated: {slack_bold_text(incident_status)}'
                else:
                    text = f'status updated: {mattermost_bold_text(incident_status)}'
                if incident_status == 'unknown':
                    if self.type == 'slack':
                        admins_ids = [a.id for a in self.admin_users]
                        admins_text = slack_env.from_string(slack_admins_template_string).render(users=admins_ids)
                        text += f'\n>_{admins_text}_'
                    else:
                        admins_names = [a.username for a in self.admin_users]
                        admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(users=admins_names)
                        text += f'\n|_{admins_text}_'
                self.post_thread(incident.channel_id, incident.ts, text)

    def new_version_notification(self, channel_id, new_tag):
        if self.type == 'slack':
            admins_ids = [a.id for a in self.admin_users]
            admins_text = slack_env.from_string(slack_admins_template_string).render(users=admins_ids)
            text = (f'New IMPulse version available: {new_tag}'
                    f'\n>_see <CHANGELOG.md|https://github.com/DiTsi/impulse/blob/main/CHANGELOG.md>_'
                    f'\n>_{admins_text}_')
            slack_send_message(self.url, channel_id, text)
        else:
            admins_names = [a.username for a in self.admin_users]
            admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(users=admins_names)
            text = (f'New IMPulse version available: {new_tag}'
                    f'\n>_see [CHANGELOG.md](https://github.com/DiTsi/impulse/blob/main/CHANGELOG.md)_'
                    f'\n>_{admins_text}_')
            mattermost_send_message(self.url, channel_id, text)

    def create_thread(self, channel_id, message, status):
        if self.type == 'slack':
            payload = slack_get_create_thread_payload(channel_id, message, status)
            response = requests.post(f'{self.url}/api/chat.postMessage', headers=slack_headers, data=json.dumps(payload))
            sleep(1)
            response_json = response.json()
            return response_json['ts']
        else:
            payload = mattermost_get_create_thread_payload(channel_id, message, status)
            response = requests.post(f'{self.url}/api/v4/posts', headers=mattermost_headers, data=json.dumps(payload))
            sleep(0.1)
            response_json = response.json()
            return response_json['id']

    def post_thread(self, channel_id, id, text):
        if self.type == 'slack':
            payload = {'channel': channel_id, 'thread_ts': id, 'text': text}
            r = requests.post(
                f'{self.url}/api/chat.postMessage',
                headers=slack_headers,
                data=json.dumps(payload)
            )
            sleep(1)
        else:
            payload = {'channel_id': channel_id, 'root_id': id, 'message': text}
            r = requests.post(
                f'{self.url}/api/v4/posts',
                headers=mattermost_headers,
                data=json.dumps(payload)
            )
            sleep(0.1)
        return r.status_code

    def update_thread(self, channel_id, id, status, message, chain_enabled=True, status_enabled=True):
        if self.type == 'slack':
            payload = slack_get_update_payload(channel_id, id, message, status, chain_enabled=True, status_enabled=True)
            requests.post(
                f'{self.url}/api/chat.update',
                headers=slack_headers,
                data=json.dumps(payload)
            )
        else:
            payload = mattermost_get_update_payload(channel_id, id, message, status, chain_enabled, status_enabled)
            requests.put(
                f'{self.url}/api/v4/posts/{id}',
                headers=mattermost_headers,
                data=json.dumps(payload)
            )
            sleep(0.1)
