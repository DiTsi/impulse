import os
from datetime import datetime

import requests

from app.incident import Incident, Incidents
from app.logger import logger
from app.queue import unix_sleep_to_timedelta, Queue
from app.slack import post_thread, update_thread, create_thread, button_handler
from config import settings, incidents_path


def queue_handle(incidents, queue_, application, webhooks):
    if len(queue_.dates) == 0:
        return
    type_, uuid_, identifier = queue_.handle()
    if type_ is not None:
        if bool(incidents) is False: #!
            pass
        incident_ = incidents.by_uuid[uuid_]
        if type_ == 0:
            status_update_datetime = (
                datetime.utcnow() + unix_sleep_to_timedelta(settings.get(f'{incident_.status}_timeout'))
            )
            queue_.put(status_update_datetime, 0, uuid_)
            new_status = incident_.set_next_status()
            if new_status == 'unknown':
                post_thread(
                    incident_.channel_id,
                    incident_.ts,
                    application.user_groups['__impulse_admins__'].unknown_status_text()
                )
            elif new_status == 'closed':
                _, uuid_ = incidents.get_by_ts(incident_.ts)
                incidents.del_by_uuid(uuid_)
                queue_.delete_by_id(uuid_)
                logger.info(f'Incident \'{uuid_}\' closed')
        elif type_ == 1:
            step = incident_.chain[identifier]
            if step['type'] != 'webhook':
                r_code = application.notify(incident_.channel_id, incident_.ts, step['type'], step['identifier'])
                incident_.chain_update(identifier, done=True, result=r_code)
            else:
                url = webhooks[step['identifier']]
                r = requests.post(f'{url}')
                incident_.chain_update(identifier, done=True, result=r.status_code)


def incident_create(application, route, incidents, queue_, alert_state):
    channel, chain_name = route.get_route(alert_state)

    channel = application.channels[channel]
    template = application.message_template
    message = template.form_message(alert_state)
    ts = create_thread(channel_id=channel['id'], message=message, status=alert_state['status'])
    status = alert_state['status']

    updated_datetime = datetime.utcnow()
    status_update_datetime = datetime.utcnow() + unix_sleep_to_timedelta(settings.get(f'{status}_timeout'))
    chain = application.chains[chain_name]
    incident_ = Incident(
        alert=alert_state, status=status, ts=ts, channel_id=channel['id'], chain=[], acknowledged=False,
        acknowledged_by=None, updated=updated_datetime, message=message, status_update_datetime=status_update_datetime
    )
    uuid_ = incidents.add(incident_)

    logger.info(f'Incident \'{uuid_}\' created:')
    [logger.info(f'  {i}: {alert_state["groupLabels"][i]}') for i in alert_state['groupLabels'].keys()]

    queue_.put(status_update_datetime, 0, uuid_)

    incident_.generate_chain(chain)
    queue_.append(uuid_, incident_.chain)
    incident_.dump(f'{incidents_path}/{uuid_}.yml')


def incident_update(uuid_, incident_, queue_, alert_state):
    new_status = alert_state['status']
    if incident_.status != new_status:
        post_thread(
            incident_.channel_id,
            incident_.ts,
            f'status updated: *{new_status}*'
        )
        if new_status == 'resolved':
            queue_.delete_by_id(uuid_)
            status_update_datetime = datetime.utcnow() + unix_sleep_to_timedelta(settings.get(f'{new_status}_timeout'))
            queue_.put(status_update_datetime, 0, uuid_)
        logger.debug(f'Incident \'{uuid_}\' updated with new status \'{new_status}\'')
    else:
        logger.debug(f'Incident \'{uuid_}\' updated with same status \'{new_status}\'')
        queue_.update(uuid_, incident_.status_update_datetime)
    update_thread(
        incident_.channel_id, incident_.ts, new_status, incident_.message,
        acknowledge=incident_.acknowledged, user_id=incident_.acknowledged_by
    )
    incident_.update(alert_state, uuid_)


def handle_alert(application, route_, incidents, queue_, alert_state):
    incident_, uuid_ = incidents.get(alert=alert_state)
    if incident_ is None:
        incident_create(application, route_, incidents, queue_, alert_state)
    else:
        incident_update(uuid_, incident_, queue_, alert_state)


def slack_handler(payload, incidents, queue_):
    incident_, uuid = incidents.get_by_ts(ts=payload['message_ts'])

    modified_message = payload.get('original_message') #!
    if modified_message['attachments'][1]['actions'][0]['text'] == 'Acknowledge':
        incident_.acknowledge(payload['user']['id'])
        queue_.delete_steps_by_id(uuid) #!
    else:
        incident_.unacknowledge()
        queue_.append(uuid, incident_.chain)
    modified_message = button_handler(payload)
    return modified_message, 200


def recreate_incidents():
    if not os.path.exists(incidents_path):
        logger.debug(f'creating incidents_directory')
        os.makedirs(incidents_path)
        logger.debug(f'created incidents_directory')
    else:
        logger.debug(f'load incidents from disk')

    incidents = Incidents([])
    for path, directories, files in os.walk(incidents_path):
        for filename in files:
            incident_ = Incident.load(f'{incidents_path}/{filename}')
            incidents.add(incident_)
    return incidents


def recreate_queue(incidents):
    logger.debug(f'Creating Queue')
    queue_ = Queue()
    if bool(incidents.by_uuid):
        for uuid_, i in incidents.by_uuid.items():
            queue_.append(uuid_, i.get_chain())
            queue_.put(i.status_update_datetime, 0, uuid_)
        logger.debug(f'Queue restored from disk')
    else:
        logger.debug(f'Empty Queue created')
    return queue_
