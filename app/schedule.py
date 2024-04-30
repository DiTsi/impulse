from datetime import datetime

from app.logger import logger
from app.queue import unix_sleep_to_timedelta


class Schedule:
    def __init__(self, datetime_, action, status):
        self.datetime = datetime_
        self.action = action
        self.status = status  # 'waiting' | 'done'

    def dump(self):
        return {
            'datetime': self.datetime,
            'action': self.action.dump(),
            'status': self.status
        }

    @classmethod
    def load(cls, dump):
        return cls(dump['datetime'], Action.load(dump['action']), dump['status'])


class Action:
    def __init__(self, id_, type_, to):
        self.id = id_
        self.type = type_
        self.to = to

    def dump(self):
        return {
            'id': self.id,
            'type': self.type,
            'to': self.to
        }

    @classmethod
    def load(cls, dump):
        return cls(dump['id'], dump['type'], dump['to'])

    def __repr__(self):
        return {
            'id': self.id,
            'type': self.type,
            'to': self.to
        }


def generate_queue(incident_uuid, units, steps):
    schedules = []
    dt = datetime.utcnow()
    for s in steps:
        if 'unit' in s:
            try:
                unit = units[s.get('unit')]
                action = Action(incident_uuid, s['action'], unit.name)
                schedules.append(Schedule(
                    datetime_=dt,
                    action=action,
                    status='waiting'
                ))
            except KeyError:
                logger.warning(f'No unit {s.get("unit")} in \'units\' section. See config.yml')
        else:
            delay = unix_sleep_to_timedelta(s.get('wait'))
            dt = dt + delay
    return schedules
