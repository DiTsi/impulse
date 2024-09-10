from time import sleep

import requests

from app.im.mattermost.config import mattermost_headers, mattermost_request_delay
from app.logging import logger


def mattermost_get_public_channels(url, team):
    try:
        response = requests.get(
            f"{url}/api/v4/teams/{team['id']}/channels",
            params={'per_page': 1000},
            headers=mattermost_headers
        )
        sleep(mattermost_request_delay)
        data = response.json()
        channels_dict = {c.get('name'): c for c in data}
        return channels_dict
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to retrieve channel list: {e}')  # !
        return dict()
