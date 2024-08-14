from datetime import datetime

from app.logging import logger
from config import timeouts
from .incident import Incident, actual_version
from .incident.incident import IncidentConfig
from .time import unix_sleep_to_timedelta


def alert_handle_create(application, route, incidents, queue_, alert_state):
    channel, chain_name = route.get_route(alert_state)

    channel = application.channels[channel]
    template = application.message_template
    message = template.form_message(alert_state)
    thread_id = application.create_thread(channel_id=channel['id'], message=message, status=alert_state['status'])
    status = alert_state['status']

    updated_datetime = datetime.utcnow()
    status_update_datetime = datetime.utcnow() + unix_sleep_to_timedelta(timeouts.get(status))
    chain = application.chains.get(chain_name)
    config = IncidentConfig(
        application_type=application.type,
        application_url=application.url,
        application_team=application.team
    )
    incident_ = Incident(
        last_state=alert_state,
        status=status,
        ts=thread_id,
        channel_id=channel['id'],
        config=config,
        chain=[],
        chain_enabled=True,
        status_enabled=True,
        updated=updated_datetime,
        status_update_datetime=status_update_datetime,
        version=actual_version
    )
    uuid_ = incidents.add(incident_)

    logger.info(f'Incident \'{uuid_}\' created. Link: {incident_.link}')
    [logger.info(f'  {i}: {alert_state["groupLabels"][i]}') for i in alert_state['groupLabels'].keys()]

    queue_.put(status_update_datetime, 'update_status', uuid_)

    incident_.generate_chain(chain)
    queue_.append(uuid_, incident_.chain)
    incident_.dump()


def alert_handle_update(uuid_, incident_, queue_, alert_state, application):
    is_state_updated, is_status_updated = incident_.update_state(alert_state)
    if is_state_updated or is_status_updated:
        application.update(
            uuid_, incident_, alert_state['status'], alert_state, is_status_updated,
            incident_.chain_enabled, incident_.status_enabled
        )
    queue_.update(uuid_, incident_.status_update_datetime, incident_.status)


def alert_handle(application, route_, incidents, queue_, alert_state):
    incident_, uuid_ = incidents.get(alert=alert_state)
    logger.debug(f'New Alertmanager event for incident {uuid_}')
    logger.debug(f'{alert_state}')
    if incident_ is None:
        alert_handle_create(application, route_, incidents, queue_, alert_state)
    else:
        alert_handle_update(uuid_, incident_, queue_, alert_state, application)
