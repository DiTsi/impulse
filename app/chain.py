from datetime import datetime, timedelta

from app.logger import logger


class Chain:
    def __init__(self, name, steps):
        self.name = name
        self.steps = steps

    def __repr__(self):
        return self.name


class Schedule:
    def __init__(self, datetime_, incident, unit, action):
        self.datetime = datetime_
        self.incident = incident
        self.unit = unit
        self.action = action  # change_status|mention|webhook

    def run_action(self):
        if self.action == 'webhook':
            pass
        elif self.action == 'mention':
            pass
        else: # change_status
            pass


def generate_queue(incident_uid, units, steps):
    schedules = []
    dt = datetime.utcnow()
    for s in steps:
        if 'unit' in s:
            try:
                unit = units[s.get('unit')]
                schedules.append(Schedule(
                    datetime_=dt,
                    incident=incident_uid,
                    unit=unit,
                    action=s.get('action')
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
