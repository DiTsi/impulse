import os

import requests
from jinja2 import Template
from requests.auth import HTTPBasicAuth


class Webhook:
    def __init__(self, url, data=None, auth=None):
        self.url = self.render(url)
        for k in data.keys():
            data[k] = self.render(data[k])
        self.data = data
        self.auth = auth

    def push(self):
        if self.auth is not None:
            u, p = self.auth.split(':')
            auth = HTTPBasicAuth(self.render(u), self.render(p))
            response = requests.post(url=self.url, data=self.data, auth=auth)
        else:
            response = requests.post(url=self.url, data=self.data)
        return response.status_code

    def render(self, custom_string):
        tmplt = Template(custom_string)
        return tmplt.render(env=os.environ)


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
