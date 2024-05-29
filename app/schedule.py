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


def generate_queue(incident_uuid, users, user_groups, steps):
    schedules = []
    dt = datetime.utcnow()
    for s in steps:
        if 'wait' in s.keys():
            delay = unix_sleep_to_timedelta(s.get('wait'))
            dt = dt + delay
        elif 'user' in s.keys():
            try:
                user = users[s.get('user')]
                schedules.append(Schedule(
                    datetime_=dt,
                    id=incident_uuid,
                    type='user',
                    notify_type='slack',
                    to=user.name,
                    status='waiting',
                    result=None
                ))
            except KeyError:
                logger.warning(f'No user {s.get("user")} in \'application.users\' section. See config.yml')
        elif 'user_group' in s.keys():
            try:
                unit_group = user_groups[s.get('user_group')]
                schedules.append(Schedule(
                    datetime_=dt,
                    id=incident_uuid,
                    type='user_group',
                    notify_type='slack',
                    to=unit_group.name,
                    status='waiting',
                    result=None
                ))
            except KeyError:
                logger.warning(f'No user_group {s.get("user_group")} in \'application.user_groups\' section. See config.yml')
    return schedules
