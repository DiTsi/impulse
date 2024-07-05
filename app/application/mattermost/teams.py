import requests

from app.logger import logger
from .config import headers


def get_team(url, team_name):
    try:
        response = requests.get(
            f'{url}/api/v4/teams',
            headers=headers
        )
        data = response.json()
        for i in data:
            if i['name'] == team_name:
                return i
        return None #!
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to retrieve teams list: {e}')  # !
        return None
