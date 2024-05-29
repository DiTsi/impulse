from app.chain import generate_chains
from app.logger import logger
from app.message_template import generate_message_templates
from app.slack import get_public_channels, get_users, generate_users, generate_user_groups, button_handler, post_thread


class Application:
    def __init__(self, type_, chains, users, user_groups, channels, message_template):
        self.type = type_
        self.users = users
        self.user_groups = user_groups
        self.chains = chains
        self.channels = channels
        self.message_template = message_template


class SlackApplication(Application):
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
                logger.warning(f'No public channel \'{ch}\' in Slack')

        # create chains
        chains = generate_chains(app_config['chains'])

        # create users, user_groups
        logger.debug(f'get Slack users using API')
        existing_users = get_users() #!
        users = generate_users(app_config['users'], existing_users)
        user_groups = generate_user_groups(app_config['user_groups'], users)

        # create channels
        channels = dict()
        for ch in channels_list:
            try:
                channels[ch] = public_channels[ch]
            except KeyError:
                logger.warning(f'No public channel \'{ch}\' in Slack')

        # create message_template
        message_template_dict = app_config['message_template']
        message_template = generate_message_templates(message_template_dict)

        super().__init__('slack', chains, users, user_groups, channels, message_template)

    def handler(self, payload, incidents, queue):
        incident, uuid = incidents.get_by_ts(ts=payload['message_ts'])
        if payload['callback_id'] == 'acknowledge': #!
            incident.acknowledged = True
            incident.acknowledged_by = payload['user']['id']

            # clear queue
            queue.delete_by_id(uuid) #!
        else:
            incident.acknowledged = False
            incident.acknowledged_by = None

            # extend queue
            pass
            # incident.set_chain(schedule_list)
            # queue.put(schedule_list)

        modified_message = button_handler(payload)
        return modified_message, 200

    def notify(self, channel_id, ts, type_, identifier):
        if type_ == 'user':
            unit = self.users[identifier]
        else:
            unit = self.user_groups[identifier]
        response_code = post_thread(channel_id, ts, unit.mention_text())
        return response_code


def generate_application(app_dict, channels_list):
    # try:
    app_type = app_dict['type']
    if app_type == 'slack':
        application = SlackApplication(
            app_dict,
            channels_list
        )
    else:
        logger.error(f'Application type \'{app_type}\' not supported\nExiting...')
        exit()
    # except KeyError:
    #     logger.error(f'Specify application type in config.yml\nExiting...')
    #     exit()
    return application
