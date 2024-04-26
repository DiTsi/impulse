from datetime import datetime, timedelta

from app.logger import logger
from app.schedule import Schedule, Action


class Queue:
    def __init__(self):
        self.dates = []
        self.schedules = []
        self.last_slack_api_request = datetime.utcnow()

    def put(self, dates, schedules):
        i = len(self.dates) - 1
        if i == -1:
            self.dates = dates
            self.schedules = schedules
        else:
            for j in range(len(dates) - 1, 0, -1):
                date = dates[j]
                schedule = schedules[j]
                while True:
                    if date > self.dates[i]:
                        dates.insert(i + 1, date)
                        schedules.insert(i + 1, schedule)
                        break
                    else:
                        i -= 1
                    if i == 0:
                        dates.insert(0, date)
                        schedules.insert(0, schedule)
                        break

    def delete(self, index):
        del self.dates[index]
        del self.schedules[index]

    def handle_first(self):
        if not self.dates:
            return None
        if self.dates[0] < datetime.utcnow():
            return self.schedules[0]


def generate_queue(incident_uuid, units, steps):
    schedules = []
    dt = datetime.utcnow()
    for s in steps:
        if 'unit' in s:
            try:
                unit = units[s.get('unit')]
                action = Action(incident_uuid, s['action'], unit)
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


def unix_sleep_to_timedelta(unix_sleep_time):
    value = int(unix_sleep_time[:-1])
    unit = unix_sleep_time[-1]
    unit_map = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
    return timedelta(**{unit_map[unit]: value})
