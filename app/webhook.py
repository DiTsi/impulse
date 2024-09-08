import os

import requests
from jinja2 import Template
from requests.auth import HTTPBasicAuth

from app.incident.incident import Incident


class Webhook:
    def __init__(self, url, data=None, auth=None):
        self._url = self.render(url)
        self._pre_render_data = data
        self._auth = auth

    def push(self, incident: Incident = None):
        rendered_data = dict()
        if self._pre_render_data:
            serialized_incident = incident.serialize() if incident else dict()
            for key, value in self._pre_render_data.items():
                rendered_data[key] = self.render(value, incident=serialized_incident)
        if self._auth is not None:
            u, p = self._auth.split(':')
            auth = HTTPBasicAuth(self.render(u), self.render(p))
            try:
                response = requests.post(url=self._url, data=rendered_data, auth=auth, timeout=1.0)
            except requests.exceptions.ConnectionError:
                return f'Connection Error', None
        else:
            try:
                response = requests.post(url=self._url, data=rendered_data, timeout=1.0)
            except requests.exceptions.ConnectionError:
                return f'Connection Error', None
        return 'ok', response.status_code

    @staticmethod
    def render(custom_string, **kwargs):
        tmplt = Template(custom_string)
        return tmplt.render(env=os.environ, **kwargs)


def generate_webhooks(webhooks_dict=None):
    webhooks = dict()
    if webhooks_dict:
        for name in webhooks_dict.keys():
            webhook_dict = webhooks_dict[name]
            url = webhook_dict.get('url')
            data = webhook_dict.get('data')
            auth = webhook_dict.get('auth')
            webhooks[name] = Webhook(url, data, auth)
    return webhooks
