from time import sleep

import requests

from app.logger import logger
from app.application.mattermost.config import headers


def get_me(url):
    response = requests.get(
        f'{url}/api/v4/users/me',
        headers=headers
    )
    sleep(0.1)
    if not response.ok:
        logger.error(f'Incorrect Mattermost response. Reason: {response.reason}')
        exit()
    json_ = response.json()
    return json_
