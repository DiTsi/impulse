from time import sleep

import requests

from app.logging import logger
from .config import slack_headers, slack_request_delay


def slack_get_public_channels(url):
    try:
        response = requests.get(
            f'{url}/api/conversations.list',
            headers=slack_headers
        )
        sleep(slack_request_delay)
        data = response.json()
        channels_list = data.get('channels', [])
        channels_dict = {c.get('name'): c for c in channels_list}
        return channels_dict
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to retrieve channel list: {e}')  # !
        return dict()
