from datetime import datetime, timedelta

from app.logger import logger


class Chain:
    def __init__(self, name, steps):
        self.name = name
        self.steps = steps

    def __repr__(self):
        return self.name


class Schedule:
    def __init__(self, datetime_, incident_uuid, unit, action, status):
        self.datetime = datetime_
        self.incident_uuid = incident_uuid
        self.unit = unit
        self.action = action  # change_status|mention|webhook
        self.status = status  # 'waiting' | 'done'

    def dump(self):
        return {
            'datetime': self.datetime,
            'unit': self.unit.name if self.unit is not None else 'None',
            'action': self.action,
            'status': self.status
        }

    @classmethod
    def load(cls, incident_uuid, dump):
        datetime_ = dump.get('datetime_')
        unit = dump.get('unit')
        action = dump.get('action')
        status = dump.get('status')
        return cls(datetime_, incident_uuid, unit, action, status)


def generate_queue(incident_uuid, units, steps):
    schedules = []
    dt = datetime.utcnow()
    for s in steps:
        if 'unit' in s:
            try:
                unit = units[s.get('unit')]
                schedules.append(Schedule(
                    datetime_=dt,
                    incident_uuid=incident_uuid,
                    unit=unit,
                    action=s.get('action'),
                    status='waiting'
                ))
            except KeyError:
                logger.warning(f'No unit {s.get("unit")} in \'units\' section. See config.yml')
        else:
            delay = unix_sleep_to_timedelta(s.get('wait'))
            dt = dt + delay
    return schedules


def unix_sleep_to_timedelta(unix_sleep_time):
    value = int(unix_sleep_time[:-1])
    unit = unix_sleep_time[-1]
    unit_map = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
    return timedelta(**{unit_map[unit]: value})
