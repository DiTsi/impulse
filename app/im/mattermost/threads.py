from app.im.colors import status_colors
from app.im.mattermost.config import buttons
from config import application


def mattermost_get_button_update_payload(body, header, status_icons, status, chain_enabled, status_enabled):
    payload = {
        'update': {
            'message': f'{status_icons} {header}',
            'props': {
                'attachments': [
                    {
                        'fallback': 'test',
                        'text': body,
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
                                    "url": f"{application.get('impulse_address')}/app",
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
                                    "url": f"{application.get('impulse_address')}/app",
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


def mattermost_get_update_payload(channel_id, thread_id, body, header, status_icons, status, chain_enabled,
                                  status_enabled):
    payload = {
        'channel_id': channel_id,
        'id': thread_id,
        'message': f'{status_icons} {header}',
        'props': {
            'attachments': [
                {
                    'fallback': 'test',
                    'text': body,
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
                                "url": f"{application.get('impulse_address')}/app",
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
                                "url": f"{application.get('impulse_address')}/app",
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


def mattermost_get_create_thread_payload(channel_id, body, header, status_icons, status):
    payload = {
        'channel_id': channel_id,
        'message': f'{status_icons} {header}',
        'props': {
            'attachments': [
                {
                    'fallback': 'test',
                    'text': body,
                    'color': status_colors.get(status),
                    'actions': [
                        {
                            "id": "chain",
                            "type": "button",
                            "name": buttons['chain']['enabled']['text'],
                            "style": buttons['chain']['enabled']['style'],
                            "integration": {
                                "url": f"{application.get('impulse_address')}/app",
                                "context": {
                                    "action": "chain"
                                }
                            }
                        },
                        {
                            "id": "status",
                            "type": "button",
                            "name": buttons['status']['enabled']['text'],
                            "style": buttons['status']['enabled']['style'],
                            "integration": {
                                "url": f"{application.get('impulse_address')}/app",
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
