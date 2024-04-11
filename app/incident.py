import json
import uuid
from datetime import datetime

import yaml

from app.slack import update_thread
from config import settings


class Incident:
    def __init__(self, alert, ts, channel_id, schedule, acknowledged, acknowledged_by, updated):
        self.last_state = alert
        self.ts = ts
        self.channel_id = channel_id
        self.update_status(alert.get('status'))  # !
        self.schedule = schedule
        self.acknowledged = acknowledged
        self.acknowledged_by = acknowledged_by
        self.updated = updated

    @classmethod
    def load(cls, dump_file):
        with open(dump_file, 'r') as f:
            content = yaml.load(f, Loader=yaml.CLoader)
            last_state = content.get('last_state')
            ts = content.get('ts')
            channel_id = content.get('channel_id')
            schedule = content.get('schedule')
            updated = content.get('updated')
            acknowledged = content.get('acknowledged')
            acknowledged_by = content.get('acknowledged_by')
        return cls(last_state, ts, channel_id, schedule, acknowledged, acknowledged_by, updated)

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

    def serialize(self):
        return {
            "last_state": self.last_state,
            "channel_id": self.channel_id,
            "schedule": self.schedule,
            "updated": self.updated,
            "acknowledged": self.acknowledged,
            "ts": self.ts
        }

    def update_status(self, status):
        if self.last_state.get('status') != status:
            if status == 'firing':
                self.schedule[0]['datetime'] = datetime.utcnow() + settings.get('firing_timeout')
            elif status == 'resolved':
                self.schedule[0]['datetime'] = datetime.utcnow() + settings.get('resolved_timeout')
            elif status == 'unknown':
                self.schedule[0]['datetime'] = datetime.utcnow() + settings.get('unknown_timeout')


class Incidents:
    def __init__(self, incidents_list):
        self.by_uuid = {gen_uuid(i.last_state.get('groupLabels')): i for i in incidents_list}
        self.by_ts = {gen_uuid(i.channel_id + i.ts): i for i in incidents_list}
        pass

    def get(self, alert=None, channel_id=None, ts=None):
        if alert is not None:
            uuid = gen_uuid(alert.get('groupLabels'))
            incident = self.by_uuid.get(uuid)
        else:
            ts_id = gen_uuid(channel_id + ts)
            incident = self.by_ts.get(ts_id)
        return incident

    def add(self, incident):
        pass
        self.by_uuid[gen_uuid(incident.last_state.get('groupLabels'))] = incident
        self.by_ts[gen_uuid(incident.channel_id + incident.ts)] = incident
        pass

    def delete(self, alert, channel_id, ts):
        if alert is not None:
            uuid = gen_uuid(alert.get('groupLabels'))
            del self.by_uuid[uuid]
            # удалится по ts?
            pass
        else:
            ts_id = gen_uuid(channel_id + ts)
            del self.by_ts[ts_id]
            # удалится по uuid?
            pass


def gen_uuid(data):
    return uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(data))
