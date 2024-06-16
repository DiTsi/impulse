from app.logger import logger
from app.slack import (get_public_channels,
                       post_thread, update_thread, admin_message)
from app.slack.chain import generate_chains
from app.slack.message_template import generate_message_template
from app.slack.user import generate_users, generate_user_groups


class SlackApplication:
    def __init__(self, app_config, channels_list):
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

        self.admin_channel_id = public_channels[app_config['admin_channel']]['id']
        self.users = users
        self.user_groups = user_groups
        self.chains = chains
        self.channels = channels
        self.message_template = message_template

    def notify(self, incident, type_, identifier):
        if type_ == 'user':
            unit = self.users[identifier]
        else:
            unit = self.user_groups[identifier]
        response_code = post_thread(incident.channel_id, incident.ts, unit.mention_text())
        return response_code

    def update(self, incident, incident_status, alert_state, updated_status, chain_enabled, status_enabled):
        text = self.message_template.form_message(alert_state)
        update_thread(incident.channel_id, incident.ts, incident_status, text, chain_enabled, status_enabled)
        if updated_status and status_enabled:
            text = f'status updated: *{incident_status}*'
            if incident_status != 'closed':
                post_thread(incident.channel_id, incident.ts, text)
            if incident_status == 'unknown':
                text = (f'<https://slack.com/archives/{incident.channel_id}/{incident.link}|Incident> status set to *unknown*')
                text += f'\n>_Check *Alertmanager\'s* `repeat_interval` option is less than *IMPulse* option `firing_timeout`_'
                admin_message(self.admin_channel_id, text)


def generate_application(app_dict, channels_list):
    app_type = app_dict['type']
    if app_type == 'slack':
        application = SlackApplication(
            app_dict,
            channels_list
        )
    else:
        logger.error(f'Application type \'{app_type}\' not supported\nExiting...')
        exit()
    return application
