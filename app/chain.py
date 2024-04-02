from datetime import datetime, timedelta


class Chain:
    def __init__(self, name, steps):
        self.name = name
        self.steps = steps

    def serialize(self):
        steps = self.generate_schedule()
        return {'name': self.name, 'schedule': steps}

    def generate_schedule(self):
        steps = []
        dt = datetime.utcnow()
        for s in self.steps:
            if 'unit' in s:
                steps.append({
                    'datetime': dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'unit': s.get('unit'),
                    'action': s.get('action')
                })
            else:
                delay = unix_sleep_to_timedelta(s.get('wait'))
                dt = dt + delay
        return steps

    def __repr__(self):
        return self.name


def unix_sleep_to_timedelta(unix_sleep_time):
    value = int(unix_sleep_time[:-1])
    unit = unix_sleep_time[-1]
    unit_map = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
    return timedelta(**{unit_map[unit]: value})
