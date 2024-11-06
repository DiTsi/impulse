from app.im.mattermost.threads import mattermost_get_button_update_payload


def mattermost_buttons_handler(app, payload, incidents, queue_):
    post_id = payload['post_id']
    incident_ = incidents.get_by_ts(ts=post_id)
    if incident_ is None:
        return payload, 200
    action = payload['context']['action']

    user_name = payload.get('user_name')
    user_id = payload.get('user_id')

    if action == 'chain':
        if incident_.chain_enabled:
            incident_.assign_user_id(user_id)
            incident_.assign_user(user_name)
            incident_.chain_enabled = False
            queue_.delete_by_id(incident_.uuid, delete_steps=True, delete_status=False)
        else:
            incident_.assign_user_id("")
            incident_.assign_user("")
            incident_.chain_enabled = True
            queue_.recreate(incident_.uuid, incident_.chain)
    elif action == 'status':
        if incident_.status_enabled:
            incident_.status_enabled = False
        else:
            incident_.status_enabled = True
    incident_.dump()
    status_icons = app.status_icons_template.form_message(incident_.last_state, incident_)
    header = app.header_template.form_message(incident_.last_state, incident_)
    message = app.body_template.form_message(incident_.last_state, incident_)
    payload = mattermost_get_button_update_payload(
        message,
        header,
        status_icons,
        incident_.status,
        incident_.chain_enabled,
        incident_.status_enabled)
    return payload, 200
