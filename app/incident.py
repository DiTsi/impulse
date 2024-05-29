import json
import os
import uuid
from datetime import datetime

import yaml

from app.logger import logger
from app.queue import unix_sleep_to_timedelta
from app.schedule import Schedule, generate_queue
from app.slack import create_thread, update_thread
from config import settings

next_status = {
    'firing': 'unknown',
    'unknown': 'resolved',
    'resolved': 'closed'
}


class Incident:
    def __init__(self, alert, status, ts, channel_id, scheduler, acknowledged, acknowledged_by, message, updated):
        self.last_state = alert
        self.ts = ts
        self.status = status
        self.channel_id = channel_id
        self.scheduler = scheduler
        self.acknowledged = acknowledged
        self.acknowledged_by = acknowledged_by
        self.updated = updated
        self.message = message
        logger.info(f'New Incident created:')
        [logger.info(f'  {i}: {alert["groupLabels"][i]}') for i in alert['groupLabels'].keys()]

    def set_queue(self, schedule_list):
        self.scheduler = [q.dump() for q in schedule_list]

    def restart_scheduler(self):
        for s in self.scheduler[1:]:
            pass

    @classmethod
    def load(cls, dump_file):
        with open(dump_file, 'r') as f:
            content = yaml.load(f, Loader=yaml.CLoader)
            last_state = content.get('last_state')
            ts = content.get('ts')
            status = content.get('status')
            message = content.get('message')
            channel_id = content.get('channel_id')
            channel_type = content.get('channel_type')
            queue = content.get('queue')
            updated = content.get('updated')
            acknowledged = content.get('acknowledged')
            acknowledged_by = content.get('acknowledged_by')
        return cls(last_state, status, ts, channel_id, channel_type, queue, acknowledged, acknowledged_by, message, updated)

    def dump(self, incident_file):
        with open(incident_file, 'w') as f:
            yaml.dump(self.serialize(), f, default_flow_style=False)

    def update(self, alert, message):
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
            "queue": self.scheduler,
            "updated": self.updated,
            "acknowledged": self.acknowledged,
            "ts": self.ts,
            "status": self.status,
            "message": self.message
        }

    def update_status(self, status):
        self.status = status
        self.scheduler[0]['datetime'] = (
            datetime.utcnow() + unix_sleep_to_timedelta(settings.get(f'{self.status}_timeout'))
        )


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

    def get_by_ts(self, ts): #!
        for k, v in self.by_uuid.items():
            if v.ts == ts:
                return v, k
        return None

    def add(self, incident):
        uuid_ = gen_uuid(incident.last_state.get('groupLabels'))
        self.by_uuid[uuid_] = incident
        # self.by_ts[gen_uuid(incident.channel_id + incident.ts)] = incident
        return uuid_

    def serialize(self):
        r = {str(k): self.by_uuid[k].serialize() for k in self.by_uuid.keys()}
        return r

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
    incident = Incident(
        alert=alert_state,
        status=alert_state['status'],
        ts=ts,
        channel_id=channel['id'],
        scheduler=[],
        acknowledged=False,
        acknowledged_by=None,
        updated=datetime.utcnow(),
        message=message
    )

    chain = application.chains[chain_name]
    uuid = incidents.add(incident)
    status = alert_state.get("status")

    schedule_list = [Schedule(
        datetime_=datetime.utcnow() + unix_sleep_to_timedelta(settings.get(f'{status}_timeout')),
        id=uuid,
        type='change_status',
        notify_type=None,
        to='unknown',
        status=status,
        result=None
    )] + generate_queue(uuid, application.users, application.user_groups, chain.steps)

    incident.set_queue(schedule_list)
    queue.put(schedule_list)
    # incident.dump(f'{incidents_directory}/{channel.name}_{ts}.yml')


def handle_existing(application, incident, alert_state):
    template = application.message_template
    if incident.last_state != alert_state:
        logger.debug(f'Incident get new state')
        incident.update(alert_state, template.form_message(alert_state))
        # incident.dump(f'{incidents_directory}/{channel.name}_{incident.ts}.yml')
    else:
        logger.debug(f'Incident get same state')


def handle_alert(application, route_, incidents, queue, alert_state):
    incident = incidents.get(alert=alert_state)
    if incident is None:
        handle_new(application, route_, incidents, queue, alert_state)
    else:
        handle_existing(application, incident, alert_state)
