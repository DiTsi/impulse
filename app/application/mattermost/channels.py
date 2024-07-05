import requests

from app.logger import logger
from .config import headers


def get_public_channels(url, team):
    try:
        response = requests.get(
            f"{url}/api/v4/teams/{team['id']}/channels", #!
            headers=headers
        )
        data = response.json()
        channels_dict = {c.get('name'): c for c in data}
        return channels_dict
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to retrieve channel list: {e}')  # !
        return []
