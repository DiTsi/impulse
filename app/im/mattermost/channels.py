from time import sleep

import requests

from app.logging import logger
from .config import mattermost_headers


def mattermost_get_public_channels(url, team):
    try:
        response = requests.get(
            f"{url}/api/v4/teams/{team['id']}/channels", #!
            headers=mattermost_headers
        )
        sleep(0.1)
        data = response.json()
        channels_dict = {c.get('name'): c for c in data}
        return channels_dict
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to retrieve channel list: {e}')  # !
        return dict()
