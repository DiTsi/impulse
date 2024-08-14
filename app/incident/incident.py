from datetime import datetime

import yaml

from app.incident.helpers import gen_uuid
from app.time import unix_sleep_to_timedelta
from config import incidents_path, timeouts


class Incident:
    next_status = {
        'firing': 'unknown',
        'unknown': 'closed',
        'resolved': 'closed'
    }

    def __init__(self, alert, status, ts, channel_id, chain, chain_enabled, status_enabled, updated,
                 status_update_datetime, application_type, application_url, application_team, version):
        self.last_state = alert
        self.ts = ts
        if application_type == 'slack':
            self.link = f'{application_url}/archives/{channel_id}/p{ts.replace(".", "")}'
        else:
            self.link = f'{application_url}/{application_team.lower()}/pl/{ts}'
        self.status = status
        self.channel_id = channel_id
        self.chain = chain
        self.chain_enabled = chain_enabled
        self.status_enabled = status_enabled
        self.status_update_datetime = status_update_datetime
        self.updated = updated
        self.uuid = gen_uuid(alert.get('groupLabels'))
        self.version = version

    def generate_chain(self, chain=None):
        if chain and chain.steps:
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
        if self.chain_enabled:
            for c in self.chain:
                if not c['done']:
                    chain.append(c)
        return chain

    def chain_put(self, index, datetime_, type_, identifier):
        self.chain.insert(
            index, {'datetime': datetime_, 'type': type_, 'identifier': identifier, 'done': False, 'result': None}
        )

    def chain_update(self, uuid_, index, done, result):
        self.chain[index]['done'] = done
        self.chain[index]['result'] = result
        self.dump()

    def set_next_status(self):
        new_status = Incident.next_status[self.status]
        r = self.update_status(new_status)
        return r

    @classmethod
    def load(cls, dump_file, application_type, application_url, application_team):
        with open(dump_file, 'r') as f:
            content = yaml.load(f, Loader=yaml.CLoader)
            last_state = content.get('last_state')
            ts = content.get('ts')
            status = content.get('status')
            channel_id = content.get('channel_id')
            chain = content.get('chain')
            updated = content.get('updated')
            chain_enabled = content.get('chain_enabled')
            status_enabled = content.get('status_enabled')
            status_update_datetime = content.get('status_update_datetime')
            version = content.get('version')
        return cls(last_state, status, ts, channel_id, chain, chain_enabled, status_enabled,
                   updated, status_update_datetime, application_type, application_url, application_team, version)

    def dump(self):
        with open(f'{incidents_path}/{self.uuid}.yml', 'w') as f:
            d = {
                "chain_enabled": self.chain_enabled,
                "chain": self.chain,
                "channel_id": self.channel_id,
                "last_state": self.last_state,
                "status_enabled": self.status_enabled,
                "status_update_datetime": self.status_update_datetime,
                "status": self.status,
                "ts": self.ts,
                "updated": self.updated,
                "version": self.version
            }
            yaml.dump(d, f, default_flow_style=False)

    def serialize(self):
        return {
            "chain_enabled": self.chain_enabled,
            "chain": self.chain,
            "channel_id": self.channel_id,
            "last_state": self.last_state,
            "link": self.link,
            "status_enabled": self.status_enabled,
            "status_update_datetime": self.status_update_datetime,
            "status": self.status,
            "ts": self.ts,
            "updated": self.updated,
        }

    def update_status(self, status):
        updated = False
        now = datetime.utcnow()
        self.updated = now
        if status != 'closed':
            self.status_update_datetime = now + unix_sleep_to_timedelta(timeouts.get(status))
        else:
            self.status_update_datetime = None
        if self.status != status:
            self.set_status(status)
            updated = True
        self.dump()
        return updated

    def update_state(self, alert_state):
        update_state = False
        update_status = False

        updated = self.update_status(alert_state['status'])
        if updated:
            update_status = True
        if self.last_state != alert_state:
            update_state = True
            self.last_state = alert_state
        return update_state, update_status

    def set_status(self, status):
        self.status = status
