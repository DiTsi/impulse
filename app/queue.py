from datetime import datetime, timedelta


class Queue:
    def __init__(self):
        self.dates = []
        self.schedules = []
        self.last_slack_api_request = datetime.utcnow()

    def put(self, schedules):
        dates = [iq.datetime for iq in schedules]

        if len(self.dates) == 0:
            self.dates = dates[1:]
            self.schedules = schedules[1:]
            del dates[1:]
            del schedules[1:]

        i = len(self.dates)
        for j in range(len(dates) - 1, -1, -1):
            date = dates[j]
            schedule = schedules[j]
            while True:
                if date > self.dates[i - 1] or i == 0:
                    self.dates.insert(i, date)
                    self.schedules.insert(i, schedule)
                    break
                else:
                    i -= 1

    def delete(self, index):
        del self.dates[index]
        del self.schedules[index]

    def handle_first(self):
        if not self.dates:
            return None
        if self.dates[0] < datetime.utcnow():
            schedule = self.schedules[0]
            self.delete(0)
            return schedule

    def serialize(self):
        l_ = list()
        for i in range(len(self.dates)):
            l_.append({'datetime': self.dates[i], 'schedule': self.schedules[i].dump()})
        return l_


def unix_sleep_to_timedelta(unix_sleep_time):
    value = int(unix_sleep_time[:-1])
    unit = unix_sleep_time[-1]
    unit_map = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
    return timedelta(**{unit_map[unit]: value})
