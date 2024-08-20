import json
from abc import ABC, abstractmethod
from time import sleep

import requests

from app.im.chain import generate_chains
from app.im.groups import generate_user_groups
from app.im.template import JinjaTemplate
from app.logging import logger
from app.text_manager import TextManager


class Application(ABC):

    def __init__(self, app_config, channels_list, default_channel):
        self.type = app_config['type']
        self.url = self.get_url(app_config)
        self.team = self.get_team_name(app_config)
        self.channels = self.get_channels(channels_list)
        self.default_channel_id = self.channels[default_channel]['id']
        self.chains = generate_chains(app_config.get('chains', dict()))
        self.users = self.generate_users(app_config.get('users'))
        self.user_groups = generate_user_groups(app_config.get('user_groups'), self.users)
        self.admin_users = [self.users[admin] for admin in app_config['admin_users']]
        self.templates = app_config.get('template_files', dict())
        self.body_template, self.header_template, self.status_icons_template = self.generate_template()

        # Application-specific parameters
        self.post_message_url = None
        self.headers = None
        self.post_delay = None
        self.thread_id_key = None

    def get_channels(self, channels_list):
        logger.debug(f'Get {self.type.capitalize()} channels using API')
        public_channels = self._get_public_channels()
        channels = {ch: public_channels[ch] for ch in channels_list if ch in public_channels}
        missing_channels = set(channels_list) - set(channels.keys())
        for ch in missing_channels:
            logger.warning(f'No public channel \'{ch}\' in {self.type.capitalize()}')
        return channels

    def get_url(self, app_config):
        logger.debug(f'Get {self.type.capitalize()} URL')
        return self._get_url(app_config)

    def get_team_name(self, app_config):
        logger.debug(f'Get {self.type.capitalize()} team name') #! disable for Slack
        return self._get_team_name(app_config)

    def generate_users(self, users_dict):
        logger.debug(f'Get {self.type.capitalize()} users using API')
        return self._generate_users(users_dict)

    def generate_template(self):
        def read_template(file_key, default_path):
            file_path = self.templates.get(file_key, default_path)
            return JinjaTemplate(open(file_path).read())

        body_template = read_template('body', f'./templates/{self.type}_body.j2')
        header_template = read_template('header', f'./templates/{self.type}_header.j2')
        status_icons_template = read_template('status_icons', f'./templates/{self.type}_status_icons.j2')

        return body_template, header_template, status_icons_template

    def notify(self, incident, notify_type, identifier):
        destinations = self.get_notification_destinations()
        if notify_type == 'user':
            unit = self.users[identifier]
            unit_text = unit.mention_text(destinations)
        else:
            unit = self.user_groups[identifier]
            unit_text = unit.mention_text(self.type, destinations)
        text = (
            f'{self._format_text_citation(self.header_template.form_message(incident.last_state))}\n'
            f'{unit_text}'
        )
        response_code = self._post_thread(incident.channel_id, incident.ts, text)
        return response_code

    def notify_webhook(self, incident, base_text, result, response_code=None):
        if result == 'ok':
            base_text += f'{response_code}'
            if response_code >= 400:
                admins_text = self.get_admins_text()
                italic_admins_text = self._format_text_italic(admins_text)
                base_text += f'\n➤ admins: {italic_admins_text}'
        else:
            base_text += f'{result}'
            admins_text = self.get_admins_text()
            italic_admins_text = self._format_text_italic(admins_text)
            base_text += f'\n➤ admins: {italic_admins_text}'
        text = (
            f'{self._format_text_citation(self.header_template.form_message(incident.last_state))}\n'
            f'{base_text}'
        )

        return self._post_thread(incident.channel_id, incident.ts, text)

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
                body = TextManager.get_template('status_update', self._format_text_citation(
                    self.header_template.form_message(incident.last_state)),
                                                self._format_text_bold(incident_status))
                if incident_status == 'unknown':
                    admins_text = self.get_admins_text()
                    italic_admins_text = self._format_text_italic(admins_text)
                    body = TextManager.get_template('unknown_status', self._format_text_citation(
                        self.header_template.form_message(incident.last_state)),
                                                    self._format_text_bold(incident_status), italic_admins_text)
                self._post_thread(incident.channel_id, incident.ts, body)

    def new_version_notification(self, channel_id, new_tag):
        r = requests.get(f'https://api.github.com/repos/DiTsi/impulse/releases/tags/{new_tag}')
        release_notes = r.json().get('body')
        new_version_text = self.format_text_bold(f'New IMPulse version available: {new_tag}')
        changelog_link_text = self._format_text_link("CHANGELOG.md",
                                                     "https://github.com/DiTsi/impulse/blob/main/CHANGELOG.md")
        text = TextManager.get_template('new_version', new_version_text, changelog_link_text, release_notes)
        admins_text = self.get_admins_text()
        italic_admins_text = self._format_text_italic(admins_text)
        self.send_message(channel_id, text, italic_admins_text)

    def create_thread(self, channel_id, body, header, status_icons, status):
        payload = self._create_thread_payload(channel_id, body, header, status_icons, status)
        response = requests.post(self.post_message_url, headers=self.headers, data=json.dumps(payload))
        sleep(self.post_delay)
        response_json = response.json()
        return response_json[self.thread_id_key]

    def update_thread(self, channel_id, id_, status, body, header, status_icons, chain_enabled=True,
                      status_enabled=True):
        payload = self._update_thread_payload(channel_id, id_, body, header, status_icons, status, chain_enabled,
                                              status_enabled)
        self._update_thread(id_, payload)

    def _post_thread(self, channel_id, id_, text):
        payload = self._post_thread_payload(channel_id, id_, text)
        response = requests.post(self.post_message_url, headers=self.headers, data=json.dumps(payload))
        sleep(self.post_delay)
        return response.status_code

    @abstractmethod
    def _get_public_channels(self):
        pass

    @abstractmethod
    def _get_url(self, app_config):
        pass

    @abstractmethod
    def _get_team_name(self, app_config):
        pass

    @abstractmethod
    def _generate_users(self, users_dict):
        pass

    @abstractmethod
    def get_notification_destinations(self):
        pass

    @abstractmethod
    def format_text_bold(self, text):
        pass

    @abstractmethod
    def _format_text_link(self, text, url):
        pass

    @abstractmethod
    def _format_text_italic(self, text):
        pass

    @abstractmethod
    def _format_text_citation(self, text):
        pass

    @abstractmethod
    def get_admins_text(self):
        pass

    @abstractmethod
    def send_message(self, channel_id, text, attachment):
        pass

    @abstractmethod
    def _create_thread_payload(self, channel_id, body, header, status_icons, status):
        pass

    @abstractmethod
    def _post_thread_payload(self, channel_id, id, text):
        pass

    @abstractmethod
    def _update_thread_payload(self, channel_id, id_, body, header, status_icons, status, chain_enabled,
                               status_enabled):
        pass

    @abstractmethod
    def _update_thread(self, id_, payload):
        pass
