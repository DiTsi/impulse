import os
import yaml

from app.logger import logger

slack_bot_user_oauth_token = os.environ.get('SLACK_BOT_USER_OAUTH_TOKEN')
slack_verification_token = os.environ.get('SLACK_VERIFICATION_TOKEN')
data_path = os.environ.get('DATA_PATH', default='./data')
config_path = os.environ.get('CONFIG_PATH', default='./')
debug_slack_mention = os.environ.get('DEBUG_SLACK_MENTION', default='False')

incidents_path = data_path + '/incidents'

with open(f'{config_path}/impulse.yml', 'r') as file:
    try:
        settings = yaml.safe_load(file)

        # status timeouts
        timeouts = {
            'firing': settings.get('firing_timeout', '6h'),
            'unknown': settings.get('unknown_timeout', '6h'),
            'resolved': settings.get('resolved_timeout', '12h'),
        }

        #
    except yaml.YAMLError as e:
        logger.error("Error reading YAML file: ", e)
