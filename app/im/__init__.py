import json
from abc import abstractmethod, ABC
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
from .message_template import generate_message_template
from .slack import slack_send_message
from .slack.buttons import slack_buttons_handler
from .slack.channels import slack_get_public_channels
from .slack.config import slack_headers, slack_bold_text, slack_admins_template_string, slack_env, slack_request_delay
from .slack.threads import slack_get_create_thread_payload
from .slack.threads import slack_get_update_payload
from .slack.user import slack_generate_users


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
        self.request_delay = None
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
                    formatted_admins_text = self._format_admins_text(admins_text)
                    text += f'\n{formatted_admins_text}'
                self.post_thread(incident.channel_id, incident.ts, text)

    @abstractmethod
    def _format_text_bold(self, text):
        pass

    @abstractmethod
    def _format_text_link(self, text, url):
        pass

    @abstractmethod
    def _get_admins_text(self):
        pass

    @abstractmethod
    def _format_admins_text(self, text):
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
        self.send_message(channel_id, text, admins_text)

    @abstractmethod
    def send_message(self, channel_id, text, attachment):
        pass

    def create_thread(self, channel_id, message, status):
        payload = self._create_thread_payload(channel_id, message, status)
        response = requests.post(self.post_message_url, headers=self.headers, data=json.dumps(payload))
        sleep(self.request_delay)
        response_json = response.json()
        return response_json[self.thread_id_key]

    @abstractmethod
    def _create_thread_payload(self, channel_id, message, status):
        pass

    def post_thread(self, channel_id, id_, text):
        payload = self._post_thread_payload(channel_id, id_, text)
        response = requests.post(self.post_message_url, headers=self.headers, data=json.dumps(payload))
        sleep(self.request_delay)
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


class SlackApplication(Application):
    def __init__(self, app_config, channels_list, default_channel):
        super().__init__(app_config, channels_list, default_channel)

        self.post_message_url = f'{self.url}/api/chat.postMessage'
        self.headers = slack_headers
        self.post_delay = slack_request_delay
        self.thread_id_key = 'ts'

    def _get_public_channels(self):
        return slack_get_public_channels(self.url)

    def _get_url(self, app_config):
        return 'https://slack.com'

    def _get_team_name(self, app_config):
        return None

    def _generate_users(self, users_dict):
        return slack_generate_users(self.url, users_dict)

    def get_notification_destinations(self):
        return [a.slack_id for a in self.admin_users]

    def _format_text_bold(self, text):
        return slack_bold_text(text)
    
    def _format_text_link(self, text, url):
        return f"(<{url}|{text}>)"

    def _get_admins_text(self):
        admins_text = slack_env.from_string(slack_admins_template_string).render(
            users=self.get_notification_destinations()
        )
        return f'_{admins_text}_'
    
    def _format_admins_text(self, text):
        return f'>{text}'

    def send_message(self, channel_id, text, attachment):
        slack_send_message(self.url, channel_id, text, attachment)

    def _create_thread_payload(self, channel_id, message, status):
        return slack_get_create_thread_payload(channel_id, message, status)

    def _post_thread_payload(self, channel_id, id, text):
        return {'channel': channel_id, 'thread_ts': id, 'text': text}

    def _update_thread_payload(self, channel_id, id_, message, status, chain_enabled, status_enabled):
        return slack_get_update_payload(channel_id, id_, message, status, chain_enabled, status_enabled)

    def _update_thread(self, id_, payload):
        requests.post(
            f'{self.url}/api/chat.update',
            headers=slack_headers,
            data=json.dumps(payload)
        )


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

    def _format_text_bold(self, text):
        return mattermost_bold_text(text)

    def _format_text_link(self, text, url):
        return f"([{text}]({url}))"

    def _get_admins_text(self):
        admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(
            users=self.get_notification_destinations()
        )
        return f'_{admins_text}_'
    
    def _format_admins_text(self, text):
        return f'|{text}'

    def send_message(self, channel_id, text, attachment):
        mattermost_send_message(self.url, channel_id, text, attachment)

    def _create_thread_payload(self, channel_id, message, status):
        return mattermost_get_create_thread_payload(channel_id, message, status)

    def _post_thread_payload(self, channel_id, id_, text):
        return {'channel_id': channel_id, 'root_id': id_, 'message': text}

    def _update_thread_payload(self, channel_id, id_, message, status, chain_enabled, status_enabled):
        return mattermost_get_update_payload(channel_id, id_, message, status, chain_enabled, status_enabled)

    def _update_thread(self, id_, payload):
        requests.put(
            f'{self.url}/api/v4/posts/{id_}',
            headers=mattermost_headers,
            data=json.dumps(payload)
        )
        sleep(self.post_delay)


def get_application(app_config, channels_list, default_channel):
    app_type = app_config['type']
    if app_type == 'slack':
        return SlackApplication(app_config, channels_list, default_channel)
    elif app_type == 'mattermost':
        return MattermostApplication(app_config, channels_list, default_channel)
    else:
        raise ValueError(f'Unknown application type: {app_type}')
