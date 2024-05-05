from datetime import datetime, timedelta


class Queue:
    def __init__(self):
        self.dates = []
        self.schedules = []
        self.last_slack_api_request = datetime.utcnow()

    def put(self, schedules):
        def insert(start_index, date_, schedule_, dates_, schedules_):
            if len(dates_) == 0:
                dates_.append(date_)
                schedules_.append(schedule_)
                return 0

            start = start_index if start_index != -1 else len(dates_) - 1

            for i_ in range(start, -1, -1):
                if date_ > dates_[i_]:
                    dates_.insert(i_ + 1, date_)
                    schedules_.insert(i_ + 1, schedule_)
                    return i

            dates_.insert(0, date_)
            schedules_.insert(0, schedule_)
            return 0

        dates = [iq.datetime for iq in schedules]

        insert(-1, dates[0], schedules[0], self.dates, self.schedules)
        del dates[0]
        del schedules[0]

        insert_i = -1
        for i in range(len(dates) - 1, -1, -1):
            insert_i = insert(insert_i, dates[i], schedules[i], self.dates, self.schedules)

        pass

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
