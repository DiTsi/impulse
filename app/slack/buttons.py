from app.logger import logger
from config import slack_verification_token, incidents_path

buttons = {
    'chain': {
        'enabled': {
            'text': '◼ Chain',
            'style': 'primary'
        },
        'disabled': {
            'text': '▶ Chain',
            'style': 'normal'  # danger
        }
    },
    'status': {
        'enabled': {
            'text': '◼ Status',
            'style': 'primary'
        },
        'disabled': {
            'text': '▶ Status',
            'style': 'normal'  # danger
        }
    }
}


def button_handler(original_message, chain_enabled, status_enabled):
    if chain_enabled:
        original_message['attachments'][1]['actions'][0]['text'] = buttons['chain']['enabled']['text']
        original_message['attachments'][1]['actions'][0]['style'] = buttons['chain']['enabled']['style']
    else:
        original_message['attachments'][1]['actions'][0]['text'] = buttons['chain']['disabled']['text']
        original_message['attachments'][1]['actions'][0]['style'] = buttons['chain']['disabled']['style']

    if status_enabled:
        original_message['attachments'][1]['actions'][1]['text'] = buttons['status']['enabled']['text']
        original_message['attachments'][1]['actions'][1]['style'] = buttons['status']['enabled']['style']
    else:
        original_message['attachments'][1]['actions'][1]['text'] = buttons['status']['disabled']['text']
        original_message['attachments'][1]['actions'][1]['style'] = buttons['status']['disabled']['style']
    return original_message


def handler(payload, incidents, queue_):
    if payload.get('token') != slack_verification_token:
        logger.error(f'Unauthorized request to \'/slack\'')
        return {}, 401

    incident_, uuid_ = incidents.get_by_ts(ts=payload['message_ts'])
    original_message = payload.get('original_message')
    actions = payload.get('actions')

    for action in actions:
        if action['name'] == 'chain':
            if incident_.chain_enabled:
                incident_.chain_enabled = False
                queue_.delete_by_id(uuid_, delete_steps=True, delete_status=False)
            else:
                incident_.chain_enabled = True
                queue_.append(uuid_, incident_.chain)
        elif action['name'] == 'status':
            if incident_.status_enabled:
                incident_.status_enabled = False
            else:
                incident_.status_enabled = True
    incident_.dump(f'{incidents_path}/{uuid_}.yml')
    modified_message = button_handler(original_message, incident_.chain_enabled, incident_.status_enabled)
    return modified_message, 200
