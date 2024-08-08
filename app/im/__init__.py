import json
from time import sleep

import requests

from app.logging import logger
from .chain import generate_chains
from .groups import generate_user_groups
from .mattermost import mattermost_send_message
from .mattermost.buttons import mattermost_buttons_handler
from .mattermost.channels import mattermost_get_public_channels
from .mattermost.config import mattermost_headers, mattermost_bold_text, mattermost_admins_template_string, \
    mattermost_env, mattermost_request_delay
from .mattermost.teams import get_team
from .mattermost.threads import mattermost_get_create_thread_payload
from .mattermost.threads import mattermost_get_update_payload
from .mattermost.user import mattermost_generate_users
from .template import generate_template
from .slack import slack_send_message
from .slack.buttons import slack_buttons_handler
from .slack.channels import slack_get_public_channels
from .slack.config import slack_headers, slack_bold_text, slack_admins_template_string, slack_env, slack_request_delay
from .slack.threads import slack_get_create_thread_payload
from .slack.threads import slack_get_update_payload
from .slack.user import slack_generate_users


class Application:
    def __init__(self, app_config, channels_list, default_channel):
        type = app_config['type']
        if type == 'slack':
            url = 'https://slack.com'
            logger.debug(f'Get {type.capitalize()} channels using API')
            public_channels = slack_get_public_channels(url)
            team_name = None
        else:
            url = app_config['url']
            team_name = app_config['team']
            team = get_team(url, team_name)
            logger.debug(f'get {type.capitalize()} channels using API')
            public_channels = mattermost_get_public_channels(url, team)

        logger.debug(f'Get channels IDs for channels in route')
        channels = dict()
        for ch in channels_list:
            try:
                channels[ch] = public_channels[ch]
            except KeyError:
                logger.warning(f'No public channel \'{ch}\' in {type.capitalize()}')

        chains = generate_chains(app_config.get('chains', dict()))
        logger.debug(f'Get {type.capitalize()} users using API')
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
                logger.warning(f'No public channel \'{ch}\' in {type.capitalize()}')

        templates = app_config.get('templates', dict())
        body_template_dict = templates.get('body')
        header_template_dict = templates.get('header')
        status_icons_template_dict = templates.get('status_icons')
        body_template, header_template, status_icons_template = generate_template(
            type, body_template_dict, header_template_dict, status_icons_template_dict
        )
        admins_list = app_config['admin_users']
        self.default_channel_id = channels[default_channel]['id']
        self.admin_users = [users[admin] for admin in admins_list]
        self.users = users
        self.user_groups = user_groups
        self.chains = chains
        self.channels = channels
        self.body_template = body_template
        self.header_template = header_template
        self.status_icons_template = status_icons_template
        self.team = team_name
        self.type = type
        self.url = url

    def notify(self, incident, notify_type, identifier):
        if self.type == 'slack':
            admins_ids = [a.slack_id for a in self.admin_users]
            if notify_type == 'user':
                unit = self.users[identifier]
                text = (f"{self.header_template.form_message(incident.last_state)}\n"
                        f"{unit.mention_text(admins_ids)}")
                response_code = self.post_thread(incident.channel_id, incident.ts, text)
                return response_code
            else:
                unit = self.user_groups[identifier]
                text = (f"{self.header_template.form_message(incident.last_state)}\n"
                        f"{unit.mention_text(self.type, admins_ids)}")
                response_code = self.post_thread(incident.channel_id, incident.ts, text)
                return response_code
        else:
            admins_names = [a.username for a in self.admin_users]
            if notify_type == 'user':
                unit = self.users[identifier]
                text = self.body_template + unit.mention_text(admins_names)
                response_code = self.post_thread(incident.channel_id, incident.ts, text)
                return response_code
            else:
                unit = self.user_groups[identifier]
                text = self.body_template + unit.mention_text(self.type, admins_names)
                response_code = self.post_thread(incident.channel_id, incident.ts, text)
                return response_code

    def update(self, uuid_, incident, incident_status, alert_state, updated_status, chain_enabled, status_enabled):
        body = self.body_template.form_message(alert_state)
        header = self.header_template.form_message(alert_state)
        status_icons = self.status_icons_template.form_message(alert_state)
        self.update_thread(
            incident.channel_id, incident.ts, incident_status, body, header, status_icons, chain_enabled, status_enabled
        )
        if updated_status:
            logger.info(f'Incident \'{uuid_}\' updated with new status \'{incident_status}\'')
            # post to thread
            if status_enabled and incident_status != 'closed':
                if self.type == 'slack':
                    body = f'status updated: {slack_bold_text(incident_status)}'
                else:
                    body = f'status updated: {mattermost_bold_text(incident_status)}'
                if incident_status == 'unknown':
                    if self.type == 'slack':
                        admins_ids = [a.slack_id for a in self.admin_users]
                        admins_text = slack_env.from_string(slack_admins_template_string).render(users=admins_ids)
                        body += f'\n>_{admins_text}_'
                    else:
                        admins_names = [a.username for a in self.admin_users]
                        admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(
                            users=admins_names
                        )
                        body += f'\n|_{admins_text}_'
                self.post_thread(incident.channel_id, incident.ts, body)

    def new_version_notification(self, channel_id, new_tag):
        r = requests.get(f'https://api.github.com/repos/DiTsi/impulse/releases/tags/{new_tag}')
        release_notes = r.json().get('body')

        if self.type == 'slack':
            admins_ids = [a.slack_id for a in self.admin_users]
            admins_text = slack_env.from_string(slack_admins_template_string).render(users=admins_ids)
            text = (
                f"*New IMPulse version available: {new_tag}* (<https://github.com/DiTsi/impulse/blob/main/CHANGELOG.md|CHANGELOG.md>)"
                f"\n\n{release_notes}"
            )
            slack_send_message(self.url, channel_id, text, f"_{admins_text}_")
        else:
            admins_names = [a.username for a in self.admin_users]
            admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(users=admins_names)
            text = (
                f'**New IMPulse version available: {new_tag}** ([CHANGELOG.md](https://github.com/DiTsi/impulse/blob/main/CHANGELOG.md))'
                f'\n\n{release_notes}'
            )
            mattermost_send_message(self.url, channel_id, text, f"_{admins_text}_")

    def create_thread(self, channel_id, body, header, status_icons, status):
        if self.type == 'slack':
            payload = slack_get_create_thread_payload(channel_id, body, header, status_icons, status)
            response = requests.post(f'{self.url}/api/chat.postMessage', headers=slack_headers, data=json.dumps(payload))
            sleep(slack_request_delay)
            response_json = response.json()
            return response_json['ts']
        else:
            payload = mattermost_get_create_thread_payload(channel_id, body, header, status_icons, status)
            response = requests.post(f'{self.url}/api/v4/posts', headers=mattermost_headers, data=json.dumps(payload))
            sleep(mattermost_request_delay)
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
            sleep(slack_request_delay)
        else:
            payload = {'channel_id': channel_id, 'root_id': id, 'message': text}
            r = requests.post(
                f'{self.url}/api/v4/posts',
                headers=mattermost_headers,
                data=json.dumps(payload)
            )
            sleep(mattermost_request_delay)
        return r.status_code

    def update_thread(self, channel_id, id, status, body, header, status_icons, chain_enabled=True, status_enabled=True):
        if self.type == 'slack':
            payload = slack_get_update_payload(channel_id, id, body, header, status_icons, status, chain_enabled, status_enabled)
            requests.post(
                f'{self.url}/api/chat.update',
                headers=slack_headers,
                data=json.dumps(payload)
            )
        else:
            payload = mattermost_get_update_payload(channel_id, id, body, header, status_icons, status, chain_enabled, status_enabled)
            requests.put(
                f'{self.url}/api/v4/posts/{id}',
                headers=mattermost_headers,
                data=json.dumps(payload)
            )
            sleep(mattermost_request_delay)
