import json
import uuid
from datetime import datetime

import yaml

from app.channel import SlackChannels
from app.slack import update_thread, create_thread
from app.slack import get_public_channels

from config import settings


public_channels_dict = get_public_channels()
public_channels = SlackChannels(public_channels_dict)


class Incident:
    def __init__(self, alert, channel, steps=None, chain=None, template=None, ts=None, updated=None):
        self.last_state = alert
        self.channel = channel
        if chain is not None:
            self.steps = chain.serialize()
        else:
            self.steps = steps
        if updated is not None:
            self.updated = updated
        else:
            self.updated = datetime.utcnow()
        if ts is not None:
            self.ts = ts
        else:
            self.ts = create_thread(
                channel_id=public_channels.get_by_name(channel).id,
                message=template.form_message(alert),
                status=alert.get('status'),
            )
        self.schedule = {}
        self.update_status(alert.get('status')) #!

    def dump(self, incidents_directory):
        with open(f'{incidents_directory}/{self.channel}_{self.ts}.yml', 'w') as f:
            yaml.dump(self.serialize(), f, default_flow_style=False)

    def update(self, alert, template):
        self.update_status(alert.get('status'))
        self.last_state = alert
        self.updated = datetime.utcnow()
        update_thread(
            channel_id=public_channels.get_by_name(self.channel).id,
            ts=self.ts,
            status=alert.get('status'),
            message=template.form_message(alert),
        )

    def serialize(self):
        return {
            "last_state": self.last_state,
            "channel": self.channel,
            "schedule": self.schedule,
            "updated": self.updated,
            "ts": self.ts
        }

    def update_status(self, status):
        if self.last_state.get('status') != status:
            if status == 'firing':
                self.schedule['update_status'] = settings.get('firing_timeout')
            elif status == 'resolved':
                self.schedule['update_status'] = settings.get('resolved_timeout')
            elif status == 'unknown':
                self.schedule['update_status'] = settings.get('unknown_timeout')


class Incidents:
    def __init__(self, incidents_list):
        self.by_uuid = {gen_uuid(i.last_state.get('groupLabels')): i for i in incidents_list}
        self.by_ts = {gen_uuid(i.channel + i.ts): i for i in incidents_list}

    def get(self, alert=None, channel=None, ts=None):
        if alert is not None:
            uuid = gen_uuid(alert.get('groupLabels'))
            incident = self.by_uuid.get(uuid)
        else:
            ts_id = gen_uuid(channel + ts)
            incident = self.by_ts.get(ts_id)
        return incident

    def add(self, incident):
        self.by_uuid[gen_uuid(incident.last_state.get('groupLabels'))] = incident
        self.by_ts[gen_uuid(incident.channel + incident.ts)] = incident

    def delete(self, alert, channel, ts):
        if alert is not None:
            uuid = gen_uuid(alert.get('groupLabels'))
            del self.by_uuid[uuid]
            # удалится по ts?
            pass
        else:
            ts_id = gen_uuid(channel + ts)
            del self.by_ts[ts_id]
            # удалится по uuid?
            pass


def gen_uuid(data):
    return uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(data))


def load_incident(file):
    with open(file, 'r') as f:
        content = yaml.load(f, Loader=yaml.CLoader)

    channel = content.get('channel')
    last_state = content.get('last_state')
    steps = content.get('steps')
    ts = content.get('ts')
    updated = content.get('updated')

    return Incident(last_state, channel, steps=steps, chain=None, template=None, ts=ts, updated=updated)
