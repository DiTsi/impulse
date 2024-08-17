import json
from abc import ABC, abstractmethod
from time import sleep

import requests

from app.im.chain import generate_chains
from app.im.groups import generate_user_groups
from app.im.message_template import generate_message_template
from app.logging import logger


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
        self.message_template = generate_message_template(type, app_config.get('message_template'))
        self.admin_users = [self.users[admin] for admin in app_config['admin_users']]

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

    @abstractmethod
    def _get_public_channels(self):
        pass

    def get_url(self, app_config):
        logger.debug(f'Get {self.type.capitalize()} URL')
        return self._get_url(app_config)

    @abstractmethod
    def _get_url(self, app_config):
        pass

    def get_team_name(self, app_config):
        logger.debug(f'Get {self.type.capitalize()} team name')
        return self._get_team_name(app_config)

    @abstractmethod
    def _get_team_name(self, app_config):
        pass

    def generate_users(self, users_dict):
        logger.debug(f'Get {self.type.capitalize()} users using API')
        return self._generate_users(users_dict)

    @abstractmethod
    def _generate_users(self, users_dict):
        pass

    def notify(self, incident, notify_type, identifier):
        destinations = self.get_notification_destinations()
        if notify_type == 'user':
            unit = self.users[identifier]
            text = unit.mention_text(destinations)
            response_code = self.post_thread(incident.channel_id, incident.ts, text)
            return response_code
        else:
            unit = self.user_groups[identifier]
            text = unit.mention_text(self.type, destinations)
            response_code = self.post_thread(incident.channel_id, incident.ts, text)
            return response_code

    @abstractmethod
    def get_notification_destinations(self):
        pass

    def update(self, uuid_, incident, incident_status, alert_state, updated_status, chain_enabled, status_enabled):
        text = self.message_template.form_message(alert_state)
        self.update_thread(incident.channel_id, incident.ts, incident_status, text, chain_enabled, status_enabled)
        if updated_status:
            logger.info(f'Incident \'{uuid_}\' updated with new status \'{incident_status}\'')
            # post to thread
            if status_enabled and incident_status != 'closed':
                text = f'status updated: {self._format_text_bold(incident_status)}'
                if incident_status == 'unknown':
                    admins_text = self._get_admins_text()
                    italic_admins_text = self._format_text_italic(admins_text)
                    formatted_admins_text = self._format_text_citation(italic_admins_text)
                    text += f'\n{formatted_admins_text}'
                self.post_thread(incident.channel_id, incident.ts, text)

    @abstractmethod
    def _format_text_bold(self, text):
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
    def _get_admins_text(self):
        pass

    def new_version_notification(self, channel_id, new_tag):
        r = requests.get(f'https://api.github.com/repos/DiTsi/impulse/releases/tags/{new_tag}')
        release_notes = r.json().get('body')
        new_version_text = self._format_text_bold(f'New IMPulse version available: {new_tag}')
        changelog_link_text = self._format_text_link("CHANGELOG.md",
                                                     "https://github.com/DiTsi/impulse/blob/main/CHANGELOG.md")
        text = (f'{new_version_text} {changelog_link_text}'
                f'\n\n{release_notes}')
        admins_text = self._get_admins_text()
        italic_admins_text = self._format_text_italic(admins_text)
        self.send_message(channel_id, text, italic_admins_text)

    @abstractmethod
    def send_message(self, channel_id, text, attachment):
        pass

    def create_thread(self, channel_id, message, status):
        payload = self._create_thread_payload(channel_id, message, status)
        response = requests.post(self.post_message_url, headers=self.headers, data=json.dumps(payload))
        sleep(self.post_delay)
        response_json = response.json()
        return response_json[self.thread_id_key]

    @abstractmethod
    def _create_thread_payload(self, channel_id, message, status):
        pass

    def post_thread(self, channel_id, id_, text):
        payload = self._post_thread_payload(channel_id, id_, text)
        response = requests.post(self.post_message_url, headers=self.headers, data=json.dumps(payload))
        sleep(self.post_delay)
        return response.status_code

    @abstractmethod
    def _post_thread_payload(self, channel_id, id, text):
        pass

    def update_thread(self, channel_id, id_, status, message, chain_enabled=True, status_enabled=True):
        payload = self._update_thread_payload(channel_id, id_, message, status, chain_enabled, status_enabled)
        self._update_thread(id_, payload)

    @abstractmethod
    def _update_thread_payload(self, channel_id, id_, message, status, chain_enabled, status_enabled):
        pass

    @abstractmethod
    def _update_thread(self, id_, payload):
        pass
