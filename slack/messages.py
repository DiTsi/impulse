import json

import requests

from config import slack_token
from slack.channels import channels


def send_slack_message(channel_name, message):
    url = 'https://slack.com/api/chat.postMessage'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {slack_token}'
    }
    payload = {
        'channel': channels.get_by_name(channel_name).id,
        'text': message
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            print(f"Failed to send message to Slack. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f'Failed to send message: {e}') #!


if __name__ == "__main__":
    message_to_send = "test"
    send_slack_message('priv', message_to_send)
