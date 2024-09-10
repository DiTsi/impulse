import requests

from app.im.mattermost.config import mattermost_headers
from app.logging import logger


def get_team(url, team_name):
    try:
        response = requests.get(
            f'{url}/api/v4/teams',
            params={'per_page': 200},
            headers=mattermost_headers
        )
        data = response.json()
        for i in data:
            if i['display_name'] == team_name:
                return i
        return None  # !
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to retrieve teams list: {e}')  # !
        return None
