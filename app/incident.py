import json
import os
import uuid
from datetime import datetime

import requests
import yaml

from app.logger import logger
from app.queue import unix_sleep_to_timedelta
from app.slack import create_thread, update_thread
from config import settings

next_status = {
    'firing': 'unknown',
    'unknown': 'resolved',
    'resolved': 'closed'
}


class Incident:
    def __init__(self, alert, status, ts, channel_id, chain, acknowledged, acknowledged_by, message, updated,
                 status_update_datetime):
        self.last_state = alert
        self.ts = ts
        self.status = status
        self.channel_id = channel_id
        self.chain = chain
        self.acknowledged = acknowledged
        self.acknowledged_by = acknowledged_by
        self.updated = updated
        self.message = message
        self.status_update_datetime = status_update_datetime
        logger.info(f'New Incident created:')
        [logger.info(f'  {i}: {alert["groupLabels"][i]}') for i in alert['groupLabels'].keys()]

    def restart_scheduler(self):
        for s in self.chain[1:]:
            pass

    def chain_put(self, index, type_, identifier):
        self.chain.insert(index, {'type': type_, 'identifier': identifier, 'done': False, 'result': None})

    def chain_update(self, index, done, result):
        self.chain[index]['done'] = done
        self.chain[index]['result'] = result

    @classmethod
    def load(cls, dump_file):
        with open(dump_file, 'r') as f:
            content = yaml.load(f, Loader=yaml.CLoader)
            last_state = content.get('last_state')
            ts = content.get('ts')
            status = content.get('status')
            message = content.get('message')
            channel_id = content.get('channel_id')
            chain = content.get('chain')
            updated = content.get('updated')
            acknowledged = content.get('acknowledged')
            acknowledged_by = content.get('acknowledged_by')
            status_update_datetime = content.get('status_update_datetime')
        return cls(last_state, status, ts, channel_id, chain, acknowledged, acknowledged_by, message,
                   updated, status_update_datetime)

    def dump(self, incident_file):
        with open(incident_file, 'w') as f:
            yaml.dump(self.serialize(), f, default_flow_style=False)

    def update_thread(self, alert, message):
        self.last_state = alert
        self.updated = datetime.utcnow()
        update_thread(
            channel_id=self.channel_id,
            ts=self.ts,
            status=alert.get('status'),
            message=message
        )
        logger.debug(f'Incident updated')

    def serialize(self):
        return {
            "last_state": self.last_state,
            "channel_id": self.channel_id,
            "chain": self.chain,
            "updated": self.updated,
            "acknowledged": self.acknowledged,
            "ts": self.ts,
            "status": self.status,
            "message": self.message,
            "status_update_datetime": self.status_update_datetime
        }

    def update_status(self, status):
        self.status = status
        self.status_update_datetime = (
            datetime.utcnow() + unix_sleep_to_timedelta(settings.get(f'{self.status}_timeout'))
        )


class Incidents:
    def __init__(self, incidents_list):
        self.by_uuid = {gen_uuid(i.last_state.get('groupLabels')): i for i in incidents_list}

    def get(self, alert):
        uuid_ = gen_uuid(alert.get('groupLabels'))
        incident = self.by_uuid.get(uuid_)
        return incident

    def get_by_ts(self, ts): #!
        for k, v in self.by_uuid.items():
            if v.ts == ts:
                return v, k
        return None

    def add(self, incident):
        uuid_ = gen_uuid(incident.last_state.get('groupLabels'))
        self.by_uuid[uuid_] = incident
        return uuid_

    def serialize(self):
        r = {str(k): self.by_uuid[k].serialize() for k in self.by_uuid.keys()}
        return r

    def delete(self, alert):
        uuid_ = gen_uuid(alert.get('groupLabels'))
        del self.by_uuid[uuid_]


def queue_handle(incidents, queue, application, webhooks):
    if len(queue.dates) == 0:
        return
    type_, incident_uuid, identifier = queue.handle()
    if type_ is not None:
        incident = incidents.by_uuid[incident_uuid]
        if type_ == 0:
            new_status = next_status[incident.status]
            incident.update_status(new_status)
        elif type_ == 1:  # slack_mention
            step = incident.chain[identifier]
            if step['type'] != 'webhook':
                r_code = application.notify(incident.channel_id, incident.ts, step['type'], step['identifier'])
                incident.chain_update(identifier, done=True, result=r_code)
            else:
                url = webhooks[step['identifier']]
                r = requests.post(f'{url}')
                # return r.status_code
                incident.chain_update(identifier, done=True, result=r.status_code)


def gen_uuid(data):
    return uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(data))


def recreate_incidents():
    incidents = Incidents([])
    incidents_directory = settings.get('incidents_directory')
    for path, directories, files in os.walk(incidents_directory):
        for filename in files:
            incidents.add(Incident.load(f'{incidents_directory}/{filename}'))
    return incidents


def handle_new(application, route, incidents, queue, alert_state):
    channel, chain_name = route.get_route(alert_state)

    channel = application.channels[channel]
    template = application.message_template
    message = template.form_message(alert_state)
    ts = create_thread(
        channel_id=channel['id'],
        message=message,
        status=alert_state['status']
    )
    status = alert_state['status']

    updated_datetime = datetime.utcnow()
    status_update_datetime = datetime.utcnow() + unix_sleep_to_timedelta(settings.get(f'{status}_timeout'))
    chain = application.chains[chain_name]
    incident = Incident(
        alert=alert_state,
        status=status,
        ts=ts,
        channel_id=channel['id'],
        chain=[],
        acknowledged=False,
        acknowledged_by=None,
        updated=updated_datetime,
        message=message,
        status_update_datetime=status_update_datetime
    )
    uuid_ = incidents.add(incident)
    queue.put(status_update_datetime, 0, uuid_)

    index = 0
    dt = datetime.utcnow()
    for s in chain.steps:
        type_ = list(s.keys())[0]
        value = list(s.values())[0]
        if type_ == 'wait':
            dt = dt + unix_sleep_to_timedelta(value)
        else:
            # if type_ == 'webhook':
            #     queue.put(dt, 2, uuid_, value)
            queue.put(dt, 1, uuid_, index)
            incident.chain_put(index=index, type_=type_, identifier=value)
            index += 1
    # incident.dump(f'{incidents_directory}/{channel.name}_{ts}.yml')


def handle_existing(application, incident, alert_state):
    template = application.message_template
    if incident.last_state != alert_state:
        logger.debug(f'Incident get new state')
        incident.update_thread(alert_state, template.form_message(alert_state))
        # incident.dump(f'{incidents_directory}/{channel.name}_{incident.ts}.yml')
    else:
        logger.debug(f'Incident get same state')


def handle_alert(application, route_, incidents, queue, alert_state):
    incident = incidents.get(alert=alert_state)
    if incident is None:
        handle_new(application, route_, incidents, queue, alert_state)
    else:
        handle_existing(application, incident, alert_state)
