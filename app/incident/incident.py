from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

import yaml

from app.incident.helpers import gen_uuid
from app.time import unix_sleep_to_timedelta
from app.tools import NoAliasDumper
from config import incidents_path, timeouts, INCIDENT_ACTUAL_VERSION


@dataclass
class IncidentConfig:
    application_type: str
    application_url: str
    application_team: str


@dataclass
class Incident:
    last_state: Dict
    status: str
    channel_id: str
    config: IncidentConfig
    chain: List[Dict] = field(default_factory=list)
    chain_enabled: bool = False
    status_enabled: bool = False
    status_update_datetime: Optional[datetime] = None
    updated: datetime = datetime.utcnow()
    version: str = INCIDENT_ACTUAL_VERSION
    uuid: str = field(init=False)
    ts: str = field(default='')
    link: str = field(default='')

    next_status = {
        'firing': 'unknown',
        'unknown': 'closed',
        'resolved': 'closed'
    }

    def __post_init__(self):
        self.uuid = gen_uuid(self.last_state.get('groupLabels'))

    def set_thread(self, thread_id: str):
        self.ts = thread_id
        self.link = self.generate_link()

    def generate_link(self) -> str:
        if self.config.application_type == 'slack':
            return f'{self.config.application_url}' + f'archives/{self.channel_id}/p{self.ts.replace(".", "")}'
        return f'{self.config.application_url}/{self.config.application_team.lower()}/pl/{self.ts}'

    def generate_chain(self, chain=None):
        if not chain or not chain.steps:
            return

        dt = datetime.utcnow()
        for index, step in enumerate(chain.steps):
            type_, value = next(iter(step.items()))
            if type_ == 'wait':
                dt += unix_sleep_to_timedelta(value)
            else:
                self.chain_put(index=index, datetime_=dt, type_=type_, identifier=value)

    def get_chain(self) -> List[Dict]:
        if not self.chain_enabled:
            return list()
        return self.chain

    def chain_put(self, index: int, datetime_: datetime, type_: str, identifier: str):
        self.chain.insert(index, {
            'datetime': datetime_,
            'type': type_,
            'identifier': identifier,
            'done': False,
            'result': None
        })

    def chain_update(self, index: int, done: bool, result: Optional[str]):
        self.chain[index]['done'] = done
        self.chain[index]['result'] = result
        self.dump()

    def set_next_status(self):
        new_status = Incident.next_status[self.status]
        return self.update_status(new_status)

    @classmethod
    def load(cls, dump_file: str, config: IncidentConfig):
        with open(dump_file, 'r') as f:
            content = yaml.load(f, Loader=yaml.CLoader)
        incident = cls(
            last_state=content.get('last_state'),
            status=content.get('status'),
            channel_id=content.get('channel_id'),
            config=config,
            chain=content.get('chain', []),
            chain_enabled=content.get('chain_enabled', False),
            status_enabled=content.get('status_enabled', False),
            status_update_datetime=content.get('status_update_datetime'),
            updated=content.get('updated'),
            version=content.get('version', INCIDENT_ACTUAL_VERSION)
        )
        incident.set_thread(content.get('ts'))
        return incident

    def dump(self):
        data = {
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
        with open(f'{incidents_path}/{self.uuid}.yml', 'w') as f:
            yaml.dump(data, f, NoAliasDumper, default_flow_style=False)

    def serialize(self) -> Dict:
        return {
            "chain_enabled": self.chain_enabled,
            "chain": self.chain,
            "channel_id": self.channel_id,
            "last_state": self.last_state,
            "status_enabled": self.status_enabled,
            "status_update_datetime": self.status_update_datetime,
            "status": self.status,
            "updated": self.updated,
            "link": self.link,
            "ts": self.ts,
        }

    def update_status(self, status: str) -> bool:
        now = datetime.utcnow()
        self.updated = now
        self.status_update_datetime = (
                now + unix_sleep_to_timedelta(timeouts.get(status))) if status != 'closed' else None
        if self.status != status:
            self.set_status(status)
            self.dump()
            return True
        self.dump()
        return False

    def update_state(self, alert_state: Dict) -> (bool, bool):
        update_status = self.update_status(alert_state['status'])
        update_state = self.last_state != alert_state
        if update_state:
            self.last_state = alert_state
        return update_state, update_status

    def set_status(self, status: str):
        self.status = status
