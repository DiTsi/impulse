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

    def __init__(self, alert, status, ts, channel_id, chain, chain_enabled, status_enabled, message, updated,
                 status_update_datetime):
        self.last_state = alert
        self.ts = ts
        self.status = status
        self.channel_id = channel_id
        self.chain = chain
        self.chain_enabled = chain_enabled
        self.status_enabled = status_enabled
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

    def get_chain(self):
        chain = []
        for c in self.chain:
            if not c['done']:
                chain.append(c)
        return self.chain

    def chain_put(self, index, datetime_, type_, identifier):
        self.chain.insert(
            index, {'datetime': datetime_, 'type': type_, 'identifier': identifier, 'done': False, 'result': None}
        )

    def chain_update(self, uuid_, index, done, result):
        self.chain[index]['done'] = done
        self.chain[index]['result'] = result
        self.dump(f'{incidents_path}/{uuid_}.yml')

    def set_next_status(self):
        new_status = Incident.next_status[self.status]
        return self.update_status(new_status)

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
            chain_enabled = content.get('chain_enabled')
            status_enabled = content.get('status_enabled')
            status_update_datetime = content.get('status_update_datetime')
        return cls(last_state, status, ts, channel_id, chain, chain_enabled, status_enabled, message,
                   updated, status_update_datetime)

    def dump(self, incident_file):
        with open(incident_file, 'w') as f:
            yaml.dump(self.serialize(), f, default_flow_style=False)

    def update_thread(self, alert, message):
        self.last_state = alert
        self.updated = datetime.utcnow()
        update_thread(
            self.channel_id,
            self.ts,
            alert.get('status'),
            message
        )
        logger.debug(f'incident updated')

    def serialize(self):
        return {
            "last_state": self.last_state,
            "channel_id": self.channel_id,
            "chain": self.chain,
            "updated": self.updated,
            "chain_enabled": self.chain_enabled,
            "status_enabled": self.status_enabled,
            "ts": self.ts,
            "status": self.status,
            "message": self.message,
            "status_update_datetime": self.status_update_datetime
        }

    def update_status(self, status):
        now = datetime.utcnow()
        if status != 'closed':
            self.status_update_datetime = now + unix_sleep_to_timedelta(settings.get(f'{status}_timeout'))
        else:
            self.status_update_datetime = None
        self.updated = now
        if self.status != status:
            self.status = status
            return True
        else:
            return False

    def update(self, alert_state, uuid_):
        """
        :return: update_state, update_status
        """
        if alert_state != self.last_state:
            status = alert_state['status']
            updated = self.update_status(status)
            self.dump(f'{incidents_path}/{uuid_}.yml')
            if updated:
                logger.debug(f'Incident \'{uuid_}\' updated with new status \'{status}\'')
                return True, True
            else:
                logger.debug(f'Incident \'{uuid_}\' updated with same status \'{status}\'')
                return True, False
        else:
            return False, False


class Incidents:
    def __init__(self, incidents_list):
        self.by_uuid = {gen_uuid(i.last_state.get('groupLabels')): i for i in incidents_list}

    def get(self, alert):
        uuid_ = gen_uuid(alert.get('groupLabels'))
        incident = self.by_uuid.get(uuid_)
        return incident, uuid_

    def get_by_ts(self, ts):  # !
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
        os.remove(f'{incidents_path}/{uuid_}.yml')
        logger.info(f'Incident \'{uuid_}\' closed')

    def serialize(self):
        r = {str(k): self.by_uuid[k].serialize() for k in self.by_uuid.keys()}
        return r


def gen_uuid(data):
    return uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(data))
