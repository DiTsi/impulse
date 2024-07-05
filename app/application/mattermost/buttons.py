from .config import buttons
from .threads import mattermost_get_button_update_payload


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


def mattermost_buttons_handler(app, payload, incidents, queue_):
    channel_id = payload['channel_id']
    post_id = payload['post_id']
    incident_, uuid_ = incidents.get_by_ts(ts=post_id)
    action = payload['context']['action']
    if action == 'chain':
        if incident_.chain_enabled:
            incident_.chain_enabled = False
            queue_.delete_by_id(uuid_, delete_steps=True, delete_status=False)
        else:
            incident_.chain_enabled = True
            queue_.append(uuid_, incident_.chain)
    elif action == 'status':
        if incident_.status_enabled:
            incident_.status_enabled = False
        else:
            incident_.status_enabled = True
    # message = app.message_template.form_message(incident_.last_state)
    # app.update_thread(channel_id, post_id, incident_.status, message, incident_.chain_enabled, incident_.status_enabled)
    # incident_.dump(f'{incidents_path}/{uuid_}.yml')
    # return {
    #         "update": {
    #             "message": 'OK',
    #             "props": {}
    #         }
    #     }
    original_message = app.message_template.form_message(incident_.last_state)
    # modified_message = reformat_message(original_message, incident_.chain_enabled, incident_.status_enabled)
    payload = mattermost_get_button_update_payload(original_message, incident_.status, incident_.chain_enabled, incident_.status_enabled)
    return payload, 200
