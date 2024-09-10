from datetime import datetime, timedelta

import requests

from app.queue.handlers.base_handler import BaseHandler


class UpdateHandler(BaseHandler):
    """
    UpdateHandler class is responsible for handling the update check.

    :param queue: Queue instance
    :param application: Application instance
    :param incidents: Incidents instance
    """
    __slots__ = ['queue', 'app', 'incidents', 'latest_tag']

    def __init__(self, queue, application, incidents):
        super().__init__(queue, application, incidents)
        self.latest_tag = {'version': None}

    def handle(self, identifier):
        current_tag = get_latest_tag()
        if identifier != 'first' and current_tag != self.latest_tag['version']:
            self.app.new_version_notification(self.queue.app.default_channel_id, current_tag)
            self.latest_tag['version'] = current_tag
        elif identifier == 'first':
            self.latest_tag['version'] = current_tag

        # Always schedule the next check update
        self.queue.put(datetime.utcnow() + timedelta(days=1), 'check_update', None, identifier=None)


def get_latest_tag():
    url = f"https://api.github.com/repos/DiTsi/impulse/tags"
    response = requests.get(url)

    if response.status_code == 200:
        tags = response.json()
        if tags:
            return tags[0]['name']
        else:
            return None
