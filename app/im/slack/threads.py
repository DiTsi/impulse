from . import buttons
from ..colors import status_colors


def slack_get_update_payload(channel_id, ts, message, status, chain_enabled=True, status_enabled=True):
    payload = {
        'channel': channel_id,
        'text': '',
        'attachments': [
            {
                'color': status_colors.get(status),
                'text': message,
                'mrkdwn_in': ['text'],
            },
            {
                'color': status_colors.get(status),
                'text': f'',
                "callback_id": "buttons",
                "actions": [
                    {
                        "name": 'chain',
                        "text": buttons['chain']['enabled']['text'] if chain_enabled else buttons['chain']['disabled']['text'],
                        "type": 'button',
                        "style": buttons['chain']['enabled']['style'] if chain_enabled else buttons['chain']['disabled']['style']
                    },
                    {
                        "name": 'status',
                        "text": buttons['status']['enabled']['text'] if status_enabled else buttons['status']['disabled']['text'],
                        "type": 'button',
                        "style": buttons['status']['enabled']['style'] if status_enabled else buttons['status']['disabled']['style'],
                    }
                ],
            },
        ],
        'ts': ts,
    }
    return payload


def slack_get_create_thread_payload(channel_id, body, header, status):
    payload = {
        'channel': channel_id,
        'text': '',
        'attachments': [
            {
                'color': status_colors.get(status),
                'text': header,
                'mrkdwn_in': ['text']
            },
            {
                'color': status_colors.get(status),
                'text': body,
                'mrkdwn_in': ['text'],
            },
            {
                'color': status_colors.get(status),
                'text': '',
                'callback_id': 'buttons',
                'actions': [
                    {
                        "name": "chain",
                        "text": buttons['chain']['enabled']['text'],
                        "type": "button",
                        "style": buttons['chain']['enabled']['style']
                    },
                    {
                        "name": "status",
                        "text": buttons['status']['enabled']['text'],
                        "type": "button",
                        "style": buttons['status']['enabled']['style']
                    }
                ]
            }
        ]
    }
    return payload


# def get_blocked_thread_payload(channel_id, message, status): #! didn't work with "return modified_message, 200"
#     payload = {
#         'channel': channel_id,
#         'text': '',
#         "attachments": [{
#             "color": status_colors.get(status),
#             "blocks": [
#                 {
#                     "type": "section",
#                     "text": {
#                         "type": "mrkdwn",
#                         "text": message
#                     }
#                 },
#                 {
#                     "type": "divider"
#                 },
#                 {
#                     "type": "actions",
#                     "elements": [
#                         {
#                             "type": "button",
#                             "text": {
#                                 "type": "plain_text",
#                                 "text": "Acknowledge",
#                                 "emoji": True
#                             }
#                         }
#                     ]
#                 },
#                 {
#                     "type": "context",
#                     "elements": [
#                         {
#                             "type": "mrkdwn",
#                             "text": "test context"
#                         }
#                     ]
#                 }
#             ]
#         }]
#     }
#     response = requests.post(
#         f'{url}/api/chat.postMessage',
#         headers=headers,
#         data=json.dumps(payload)
#     )
#     return payload
