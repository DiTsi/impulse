from datetime import datetime, timedelta


class Chain:
    def __init__(self, name, steps):
        self.name = name
        self.steps = steps

    def generate_schedules(self):
        steps = []
        dt = datetime.utcnow()
        webhooks = []
        mentions = []
        for s in self.steps:
            if 'unit' in s:
                if s['action'] == 'mention':
                    mentions.append(s.get('unit'))
                elif s['action'] == 'webhook':
                    webhooks.append(s.get('unit'))
            else:
                if len(mentions) > 0:
                    steps.append({'action': 'mention', 'units': mentions, 'datetime': dt, 'status': 'waiting'})
                    mentions = []
                if len(webhooks) > 0:
                    steps.append({'action': 'webhook', 'units': webhooks, 'datetime': dt, 'status': 'waiting'})
                    webhooks = []
            if 'wait' in s:
                delay = unix_sleep_to_timedelta(s.get('wait'))
                dt = dt + delay
        if len(mentions) > 0:
            steps.append({'action': 'mention', 'units': mentions, 'datetime': dt, 'status': 'waiting'})
        if len(webhooks) > 0:
            steps.append({'action': 'webhook', 'units': webhooks, 'datetime': dt, 'status': 'waiting'})
        return steps

    def __repr__(self):
        return self.name


def unix_sleep_to_timedelta(unix_sleep_time):
    value = int(unix_sleep_time[:-1])
    unit = unix_sleep_time[-1]
    unit_map = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
    return timedelta(**{unit_map[unit]: value})
