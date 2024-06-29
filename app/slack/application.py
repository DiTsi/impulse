from app.logger import logger
from app.slack import (get_public_channels,
                       post_thread, update_thread)
from app.slack.chain import generate_chains
from app.slack.message_template import generate_message_template
from app.slack.user import admins_template_string, env
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

        admins_list = app_config['admin_users']
        self.admin_users = [users[admin] for admin in admins_list]
        self.users = users
        self.user_groups = user_groups
        self.chains = chains
        self.channels = channels
        self.message_template = message_template

    def notify(self, incident, type_, identifier):
        admins_ids = [a.slack_id for a in self.admin_users]
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
        update_thread(incident.channel_id, incident.ts, incident_status, text, chain_enabled, status_enabled)
        if updated_status:
            logger.info(f'Incident \'{uuid_}\' updated with new status \'{incident_status}\'')
            # post to thread
            if status_enabled and incident_status != 'closed':
                text = f'status updated: *{incident_status}*'
                if incident_status == 'unknown':
                    admins_ids = [a.slack_id for a in self.admin_users]
                    admins_text = env.from_string(admins_template_string).render(users=admins_ids)
                    text += f'\n>_{admins_text}_'
                post_thread(incident.channel_id, incident.ts, text)


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
