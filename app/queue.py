from datetime import datetime


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
