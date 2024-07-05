from config import impulse_url
from ..colors import status_colors
from .config import buttons


def mattermost_get_button_update_payload(message, status, chain_enabled, status_enabled):
    payload = {
        'update': {
            'message': '',
            'props': {
                'attachments': [
                    {
                        'fallback': 'test',
                        'text': message,
                        'color': status_colors.get(status),
                        'actions': [
                            {
                                "id": "chain",
                                "type": "button",
                                "name": buttons['chain']['enabled']['text'] if chain_enabled else
                                buttons['chain']['disabled']['text'],
                                "style": buttons['chain']['enabled']['style'] if chain_enabled else
                                buttons['chain']['disabled']['style'],
                                "integration": {
                                    "url": f"{impulse_url}/app",
                                    "context": {
                                        "action": "chain"
                                    }
                                }
                            },
                            {
                                "id": "status",
                                "type": "button",
                                "name": buttons['status']['enabled']['text'] if status_enabled else
                                buttons['status']['disabled']['text'],
                                "style": buttons['status']['enabled']['style'] if status_enabled else
                                buttons['status']['disabled']['style'],
                                "integration": {
                                    "url": f"{impulse_url}/app",
                                    "context": {
                                        "action": "status"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
    }
    return payload


def mattermost_get_update_payload(channel_id, id, message, status, chain_enabled, status_enabled):
    payload = {
        'channel': channel_id,
        'id': id,
        'message': '',
        'props': {
            'attachments': [
                {
                    'fallback': 'test',
                    'text': message,
                    'color': status_colors.get(status),
                    'actions': [
                        {
                            "id": "chain",
                            "type": "button",
                            "name": buttons['chain']['enabled']['text'] if chain_enabled else
                            buttons['chain']['disabled']['text'],
                            "style": buttons['chain']['enabled']['style'] if chain_enabled else
                            buttons['chain']['disabled']['style'],
                            "integration": {
                                "url": f"{impulse_url}/app",
                                "context": {
                                    "action": "chain"
                                }
                            }
                        },
                        {
                            "id": "status",
                            "type": "button",
                            "name": buttons['status']['enabled']['text'] if status_enabled else
                            buttons['status']['disabled']['text'],
                            "style": buttons['status']['enabled']['style'] if status_enabled else
                            buttons['status']['disabled']['style'],
                            "integration": {
                                "url": f"{impulse_url}/app",
                                "context": {
                                    "action": "status"
                                }
                            }
                        }
                    ]
                }
            ]
        }
    }
    return payload


def mattermost_get_create_thread_payload(channel_id, message, status):
    payload = {
        'channel_id': channel_id,
        'message': '',
        'props': {
            'attachments': [
                {
                    'fallback': 'test',
                    'text': message,
                    'color': status_colors.get(status),
                    'actions': [
                        {
                            "id": "chain",
                            "type": "button",
                            "name": buttons['chain']['enabled']['text'],
                            "style": "good",  # good, warning, danger, default, primary, and success
                            "integration": {
                                "url": f"{impulse_url}/app",
                                "context": {
                                    "action": "chain"
                                }
                            }
                        },
                        {
                            "id": "status",
                            "type": "button",
                            "name": buttons['status']['enabled']['text'],
                            "style": "good",  # good, warning, danger, default, primary, and success
                            "integration": {
                                "url": f"{impulse_url}/app",
                                "context": {
                                    "action": "status"
                                }
                            }
                        }
                    ]
                }
            ]
        }
    }
    return payload
