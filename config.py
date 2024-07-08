import os

import yaml
from dotenv import load_dotenv

from app.logging import logger

load_dotenv()

slack_bot_user_oauth_token = os.getenv('SLACK_BOT_USER_OAUTH_TOKEN')
slack_verification_token = os.getenv('SLACK_VERIFICATION_TOKEN')
mattermost_access_token = os.getenv('MATTERMOST_ACCESS_TOKEN')
# mattermost_token_id = os.getenv('MATTERMOST_TOKEN_ID') #!
data_path = os.getenv('DATA_PATH', default='./data')
config_path = os.getenv('CONFIG_PATH', default='./')

incidents_path = data_path + '/incidents'

with open(f'{config_path}/impulse.yml', 'r') as file:
    try:
        settings = yaml.safe_load(file)
        timeouts = {
            'firing': settings.get('timeouts', {}).get('firing', '6h'),
            'unknown': settings.get('timeouts', {}).get('unknown', '6h'),
            'resolved': settings.get('timeouts', {}).get('resolved', '12h'),
        }
        check_updates = settings.get('check_updates', True)
        impulse_url = settings.get('url', None)
    except yaml.YAMLError as e:
        logger.error("Error reading YAML file: ", e)
