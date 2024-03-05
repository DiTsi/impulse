import os
import yaml


slack_token = os.environ.get('SLACK_BOT_USER_OAUTH_TOKEN')


with open('config.yml', 'r') as file:
    try:
        settings = yaml.safe_load(file)
    except yaml.YAMLError as e:
        print("Error reading YAML file:", e) #!
