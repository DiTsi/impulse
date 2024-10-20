from app.im.slack.config import buttons
from app.logging import logger
from config import slack_verification_token


def reformat_message(original_message, chain_enabled, status_enabled):
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


def slack_buttons_handler(payload, incidents, queue_):
    if payload.get('token') != slack_verification_token:
        logger.error(f'Unauthorized request to \'/slack\'')
        return {}, 401

    incident_ = incidents.get_by_ts(ts=payload['message_ts'])
    original_message = payload.get('original_message')
    actions = payload.get('actions')

    for action in actions:
        if action['name'] == 'chain':
            if incident_.chain_enabled:
                incident_.chain_enabled = False
                queue_.delete_by_id(incident_.uuid, delete_steps=True, delete_status=False)
            else:
                incident_.chain_enabled = True
                queue_.recreate(incident_.uuid, incident_.chain)
        elif action['name'] == 'status':
            if incident_.status_enabled:
                incident_.status_enabled = False
            else:
                incident_.status_enabled = True
    incident_.dump()
    modified_message = reformat_message(original_message, incident_.chain_enabled, incident_.status_enabled)
    return modified_message, 200
