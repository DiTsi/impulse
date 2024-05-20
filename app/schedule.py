from datetime import datetime

from app.logger import logger
from app.queue import unix_sleep_to_timedelta


class Schedule:
    def __init__(self, datetime_, id, type, notify_type, to, status, result):
        self.datetime = datetime_
        self.id = id
        self.type = type
        self.notify_type = notify_type
        self.to = to
        self.status = status  # 'waiting' | 'done'
        self.result = result

    def dump(self):
        return {
            'datetime': self.datetime,
            'id': self.id,
            'type': self.type,
            'notify_type': self.notify_type,
            'to': self.to,
            'status': self.status,
            'result': self.result
        }

    @classmethod
    def load(cls, dump):
        return cls(
            dump['datetime'],
            dump['id'],
            dump['type'],
            dump['notify_type'],
            dump['to'],
            dump['status'],
            dump['result']
        )


def generate_queue(incident_uuid, units, unit_groups, steps):
    schedules = []
    dt = datetime.utcnow()
    for s in steps:
        if 'wait' in s:
            delay = unix_sleep_to_timedelta(s.get('wait'))
            dt = dt + delay
        elif 'unit' in s:
            try:
                unit = units[s.get('unit')]
                schedules.append(Schedule(
                    datetime_=dt,
                    id=incident_uuid,
                    type='unit',
                    notify_type=s['notify_type'],
                    to=unit.name,
                    status='waiting',
                    result=None
                ))
            except KeyError:
                logger.warning(f'No unit {s.get("unit")} in \'units\' section. See config.yml')
        elif 'unit_group' in s:
            try:
                unit_group = unit_groups[s.get('unit_group')]
                schedules.append(Schedule(
                    datetime_=dt,
                    id=incident_uuid,
                    type='unit_group',
                    notify_type=s['notify_type'],
                    to=unit_group.name,
                    status='waiting',
                    result=None
                ))
            except KeyError:
                logger.warning(f'No unit_group {s.get("unit_group")} in \'unit_groups\' section. See config.yml')
    return schedules
