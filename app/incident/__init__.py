import json
import os
import uuid
from datetime import datetime

import yaml

from app.logger import logger
from app.queue import unix_sleep_to_timedelta
from app.slack import update_thread
from config import settings, incidents_path


class Incident:
    next_status = {
        'firing': 'unknown',
        'unknown': 'closed',
        'resolved': 'closed'
    }

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

    def acknowledge(self, user_id):
        self.acknowledged = True
        self.acknowledged_by = user_id

    def unacknowledge(self):
        self.acknowledged = False
        self.acknowledged_by = None

    def chain_update(self, index, done, result):
        self.chain[index]['done'] = done
        self.chain[index]['result'] = result

    def set_next_status(self):
        new_status = Incident.next_status[self.status]
        self.update_status(new_status)
        update_thread(
            self.channel_id, self.ts, new_status, self.message,
            acknowledge=self.acknowledged, user_id=self.acknowledged_by
        )
        return new_status

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

    def update(self, alert_state, uuid_):
        status = alert_state['status']
        self.update_status(status)
        if alert_state != self.last_state:
            update_thread(self.channel_id, self.ts, self.status, self.message, self.acknowledged, self.acknowledged_by)
        self.dump(f'{incidents_path}/{uuid_}.yml')


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

    def del_by_ts(self, ts):
        _, uuid_ = self.get_by_ts(ts) #!
        self.del_by_uuid(uuid_)

    def serialize(self):
        r = {str(k): self.by_uuid[k].serialize() for k in self.by_uuid.keys()}
        return r


def gen_uuid(data):
    return uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(data))


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
            incidents.add(Incident.load(f'{incidents_path}/{filename}'))
    return incidents
