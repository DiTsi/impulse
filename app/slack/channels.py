from time import sleep

import requests

from app.logger import logger
from .config import headers, url


def get_public_channels():
    try:
        response = requests.get(
            f'{url}/api/conversations.list',
            headers=headers
        )
        sleep(1.5)
        data = response.json()
        channels_list = data.get('channels', [])
        channels_dict = {c.get('name'): c for c in channels_list}
        return channels_dict
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to retrieve channel list: {e}')  # !
        return []
