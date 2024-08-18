from app.im.mattermost.threads import mattermost_get_button_update_payload


def mattermost_buttons_handler(app, payload, incidents, queue_):
    post_id = payload['post_id']
    incident_ = incidents.get_by_ts(ts=post_id)
    action = payload['context']['action']
    if action == 'chain':
        if incident_.chain_enabled:
            incident_.chain_enabled = False
            queue_.delete_by_id(incident_.uuid, delete_steps=True, delete_status=False)
        else:
            incident_.chain_enabled = True
            queue_.append(incident_.uuid, incident_.chain)
    elif action == 'status':
        if incident_.status_enabled:
            incident_.status_enabled = False
        else:
            incident_.status_enabled = True
    incident_.dump()
    status_icons = app.status_icons_template.form_message(incident_.last_state)
    header = app.header_template.form_message(incident_.last_state)
    message = app.body_template.form_message(incident_.last_state)
    payload = mattermost_get_button_update_payload(
        message,
        header,
        status_icons,
        incident_.status,
        incident_.chain_enabled,
        incident_.status_enabled)
    return payload, 200
