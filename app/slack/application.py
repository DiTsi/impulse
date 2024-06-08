from app.logger import logger
from app.slack import (get_public_channels,
                       post_thread, update_thread)
from app.slack.chain import generate_chains
from app.slack.message_template import generate_message_template
from app.slack.user import get_users, generate_users, generate_user_groups, generate_admin_group


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
        chains = generate_chains(app_config['chains'])

        # create users, user_groups
        logger.debug(f'get Slack users using API')
        existing_users = get_users() #!
        users = generate_users(app_config['users'], existing_users)
        user_groups = generate_user_groups(app_config['user_groups'], users)
        user_groups['__impulse_admins__'] = generate_admin_group(app_config['admin_users'], users)

        # create channels
        channels = dict()
        for ch in channels_list:
            try:
                channels[ch] = public_channels[ch]
            except KeyError:
                logger.warning(f'no public channel \'{ch}\' in Slack')

        # create message_template
        message_template_dict = app_config['message_template']
        message_template = generate_message_template(message_template_dict)

        self.users = users
        self.user_groups = user_groups
        self.chains = chains
        self.channels = channels
        self.message_template = message_template

    def notify(self, channel_id, ts, type_, identifier):
        if type_ == 'user':
            unit = self.users[identifier]
        else:
            unit = self.user_groups[identifier]
        response_code = post_thread(channel_id, ts, unit.mention_text())
        return response_code

    def update(self, channel_id, ts, incident_status, alert_state, updated_status, acknowledge, user_id):
        text = self.message_template.form_message(alert_state)
        update_thread(channel_id, ts, incident_status, text, acknowledge, user_id)
        if updated_status:
            text = f'status updated: *{incident_status}*'
        if incident_status == 'unknown':
            text += f'\n{self.user_groups["__impulse_admins__"].unknown_status_text()}'
        if incident_status != 'closed':
            post_thread(channel_id, ts, text)


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
