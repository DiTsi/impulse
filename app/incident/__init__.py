import json
import os
import uuid
from datetime import datetime

import requests
import yaml

from app.logger import logger
from app.queue import unix_sleep_to_timedelta
from app.slack import create_thread, update_thread, post_thread
from config import settings, data_path

next_status = {
    'firing': 'unknown',
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
        logger.info(f'new Incident created:')
        [logger.info(f'  {i}: {alert["groupLabels"][i]}') for i in alert['groupLabels'].keys()]

    def generate_chain(self, chain):
        index = 0
        dt = datetime.utcnow()
        for s in chain.steps:
            type_ = list(s.keys())[0]
            value = list(s.values())[0]
            if type_ == 'wait':
                dt = dt + unix_sleep_to_timedelta(value)
            else:
                self.chain_put(index=index, datetime_=dt, type_=type_, identifier=value)
                index += 1
        return self.chain

    def chain_put(self, index, datetime_, type_, identifier):
        self.chain.insert(
            index, {'datetime': datetime_, 'type': type_, 'identifier': identifier, 'done': False, 'result': None}
        )

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
        logger.debug(f'incident updated')

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
        now = datetime.utcnow()
        if status == 'unknown' or status == 'closed':
            self.status_update_datetime = None
        else:
            self.status_update_datetime = now + unix_sleep_to_timedelta(settings.get(f'{status}_timeout'))
        self.status = status
        self.updated = now

    def update(self, alert_state):
        status = alert_state['status']
        self.update_status(status)
        if alert_state != self.last_state:
            update_thread(self.channel_id, self.ts, self.status, self.message, self.acknowledged, self.acknowledged_by)


class Incidents:
    def __init__(self, incidents_list):
        self.by_uuid = {gen_uuid(i.last_state.get('groupLabels')): i for i in incidents_list}

    def get(self, alert):
        uuid_ = gen_uuid(alert.get('groupLabels'))
        incident = self.by_uuid.get(uuid_)
        return incident, uuid_

    def get_by_ts(self, ts): #!
        for k, v in self.by_uuid.items():
            if v.ts == ts:
                return v, k
        return None

    def add(self, incident):
        uuid_ = gen_uuid(incident.last_state.get('groupLabels'))
        self.by_uuid[uuid_] = incident
        return uuid_

    def del_by_uuid(self, uuid_):
        del self.by_uuid[uuid_]

    def serialize(self):
        r = {str(k): self.by_uuid[k].serialize() for k in self.by_uuid.keys()}
        return r


def queue_handle(incidents, queue, application, webhooks):
    if len(queue.dates) == 0:
        return
    type_, incident_uuid, identifier = queue.handle()
    if type_ is not None:
        incident = incidents.by_uuid[incident_uuid]
        if type_ == 0:
            new_status = next_status[incident.status]
            incident.update_status(new_status)
            update_thread(
                incident.channel_id, incident.ts, new_status, incident.message,
                acknowledge=incident.acknowledged, user_id=incident.acknowledged_by
            )
            if new_status == 'unknown':
                post_thread(
                    incident.channel_id, incident.ts, application.user_groups['__impulse_admins__'].unknown_status_text()
                )
            if new_status == 'closed':
                _, uuid_ = incidents.get_by_ts(incident.ts) #!
                incidents.del_by_uuid(uuid_)
        elif type_ == 1:
            step = incident.chain[identifier]
            if step['type'] != 'webhook':
                r_code = application.notify(incident.channel_id, incident.ts, step['type'], step['identifier'])
                incident.chain_update(identifier, done=True, result=r_code)
            else:
                url = webhooks[step['identifier']]
                r = requests.post(f'{url}')
                incident.chain_update(identifier, done=True, result=r.status_code)


def gen_uuid(data):
    return uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(data))


def recreate_incidents():
    if not os.path.exists(data_path):
        logger.debug(f'creating incidents_directory')
        os.makedirs(data_path)
        logger.debug(f'created incidents_directory')
    else:
        logger.debug(f'load incidents from disk')

    incidents = Incidents([])
    incidents_directory = "data/incidents"
    for path, directories, files in os.walk(incidents_directory):
        for filename in files:
            incidents.add(Incident.load(f'{incidents_directory}/{filename}'))
    return incidents


def create_new(application, route, incidents, queue, alert_state):
    channel, chain_name = route.get_route(alert_state)

    channel = application.channels[channel]
    template = application.message_template
    message = template.form_message(alert_state)
    ts = create_thread(channel_id=channel['id'], message=message, status=alert_state['status'])
    status = alert_state['status']

    updated_datetime = datetime.utcnow()
    status_update_datetime = datetime.utcnow() + unix_sleep_to_timedelta(settings.get(f'{status}_timeout'))
    chain = application.chains[chain_name]
    incident = Incident(
        alert=alert_state, status=status, ts=ts, channel_id=channel['id'], chain=[], acknowledged=False,
        acknowledged_by=None, updated=updated_datetime, message=message, status_update_datetime=status_update_datetime
    )
    uuid_ = incidents.add(incident)
    queue.put(status_update_datetime, 0, uuid_)

    queue_chain = incident.generate_chain(chain)
    queue.recreate(uuid_, queue_chain)
    # incident.dump(f'{data_path}/incidents/{channel.name}_{ts}.yml')


def handle_existing(uuid_, incident, queue, alert_state):
    new_status = alert_state['status']
    if incident.status != new_status:
        logger.debug(f'incident get new state')
        if new_status == 'firing' and incident.status == 'resolved':
            queue.delete_by_id(uuid_)
            # incident._chain()
        elif new_status == 'resolved':
            queue.delete_by_id(uuid_)
            status_update_datetime = datetime.utcnow() + unix_sleep_to_timedelta(settings.get(f'{new_status}_timeout'))
            queue.put(status_update_datetime, 0, uuid_)
        # incident.dump(f'{data_path}/incidents/{incident.channel_id}_{incident.ts}.yml')
    else:
        logger.debug(f'incident get same state')
        update_thread(
            incident.channel_id, incident.ts, new_status, incident.message,
            acknowledge=incident.acknowledged, user_id=incident.acknowledged_by
        )
        incident.update_status(alert_state['status'])
        queue.update(uuid_, incident.status_update_datetime)
    incident.update(alert_state)


def handle_alert(application, route_, incidents, queue, alert_state):
    incident, uuid = incidents.get(alert=alert_state)
    if incident is None:
        create_new(application, route_, incidents, queue, alert_state)
    else:
        handle_existing(uuid, incident, queue, alert_state)
