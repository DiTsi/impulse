import os
import yaml

from app.logger import logger

slack_bot_user_oauth_token = os.environ.get('SLACK_BOT_USER_OAUTH_TOKEN')
slack_verification_token = os.environ.get('SLACK_VERIFICATION_TOKEN')


with open('config.yml', 'r') as file:
    try:
        settings = yaml.safe_load(file)
    except yaml.YAMLError as e:
        logger.error("Error reading YAML file: ", e)
