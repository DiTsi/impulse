from app import logger
from .mattermost import MattermostApplication
from .slack import SlackApplication


def generate_application(app_dict, channels_list, default_channel):
    app_type = app_dict['type']
    if app_type == 'slack':
        application = SlackApplication(
            app_dict,
            channels_list,
            default_channel
        )
    elif app_type == 'mattermost':
        application = MattermostApplication(
            app_dict,
            channels_list,
            default_channel
        )
    else:
        logger.error(f'Application type \'{app_type}\' not supported\nExiting...')
        exit()
    return application
