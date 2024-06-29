import os
import yaml

from app.logger import logger

slack_bot_user_oauth_token = os.environ.get('SLACK_BOT_USER_OAUTH_TOKEN')
slack_verification_token = os.environ.get('SLACK_VERIFICATION_TOKEN')
data_path = os.environ.get('DATA_PATH', default='./data')
config_path = os.environ.get('CONFIG_PATH', default='./')

incidents_path = data_path + '/incidents'

with open(f'{config_path}/impulse.yml', 'r') as file:
    try:
        settings = yaml.safe_load(file)
        timeouts = {
            'firing': settings.get('timeouts', {}).get('firing', '6h'),
            'unknown': settings.get('timeouts', {}).get('unknown', '6h'),
            'resolved': settings.get('timeouts', {}).get('resolved', '12h'),
        }
    except yaml.YAMLError as e:
        logger.error("Error reading YAML file: ", e)
