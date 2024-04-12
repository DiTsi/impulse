import json
import uuid
from datetime import datetime

import yaml

from app.logger import logger
from app.slack import update_thread
from config import settings


class Incident:
    def __init__(self, alert, ts, channel_id, queue, acknowledged, acknowledged_by, updated):
        self.last_state = alert
        self.ts = ts
        self.channel_id = channel_id
        self.update_status(alert.get('status')) #!
        self.queue = queue
        self.acknowledged = acknowledged
        self.acknowledged_by = acknowledged_by
        self.updated = updated
        logger.debug(f'New Incident created')

    def add_queue(self, queue):
        self.queue = queue

    @classmethod
    def load(cls, dump_file):
        with open(dump_file, 'r') as f:
            content = yaml.load(f, Loader=yaml.CLoader)
            last_state = content.get('last_state')
            ts = content.get('ts')
            channel_id = content.get('channel_id')
            queue = content.get('queue')
            updated = content.get('updated')
            acknowledged = content.get('acknowledged')
            acknowledged_by = content.get('acknowledged_by')
        return cls(last_state, ts, channel_id, queue, acknowledged, acknowledged_by, updated)

    def dump(self, incident_file):
        with open(incident_file, 'w') as f:
            yaml.dump(self.serialize(), f, default_flow_style=False)

    def update(self, alert, message):
        self.last_state = alert
        self.update_status(alert.get('status'))
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
            "queue": self.queue,
            "updated": self.updated,
            "acknowledged": self.acknowledged,
            "ts": self.ts
        }

    def update_status(self, status):
        if self.last_state.get('status') != status:
            if status == 'firing':
                self.queue[0]['datetime'] = datetime.utcnow() + settings.get('firing_timeout')
            elif status == 'resolved':
                self.queue[0]['datetime'] = datetime.utcnow() + settings.get('resolved_timeout')
            elif status == 'unknown':
                self.queue[0]['datetime'] = datetime.utcnow() + settings.get('unknown_timeout')


class Incidents:
    def __init__(self, incidents_list):
        self.by_uuid = {gen_uuid(i.last_state.get('groupLabels')): i for i in incidents_list}
        # self.by_ts = {gen_uuid(i.channel_id + i.ts): i for i in incidents_list}
        pass

    def get(self, alert):
        uuid_ = gen_uuid(alert.get('groupLabels'))
        incident = self.by_uuid.get(uuid_)
        # ts_id = gen_uuid(channel_id + ts)
        # incident = self.by_ts.get(ts_id)
        return incident

    def add(self, incident):
        uuid_ = gen_uuid(incident.last_state.get('groupLabels'))
        self.by_uuid[uuid_] = incident
        # self.by_ts[gen_uuid(incident.channel_id + incident.ts)] = incident
        return uuid_

    def delete(self, alert):
        uuid_ = gen_uuid(alert.get('groupLabels'))
        del self.by_uuid[uuid_]
        # удалится по ts?
        pass
        # ts_id = gen_uuid(channel_id + ts)
        # del self.by_ts[ts_id]
        # удалится по uuid?


def gen_uuid(data):
    return uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(data))
