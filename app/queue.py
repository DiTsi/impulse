from datetime import datetime, timedelta


class Queue:
    TYPES = {
        0: 'update_status',
        1: 'chain_step',
        2: 'webhook'
    }

    def __init__(self):
        self.dates = []
        self.types = []
        self.incident_uuids = []
        self.identifiers = []

    def put(self, datetime_, type_, incident_uuid, identifier=None):
        for i in range(len(self.dates)):
            if datetime_ < self.dates[i]:
                self.dates.insert(i, datetime_)
                self.types.insert(i, type_)
                self.incident_uuids.insert(i, incident_uuid)
                self.identifiers.insert(i, identifier)
                return
        self.dates.append(datetime_)
        self.types.append(type_)
        self.incident_uuids.append(incident_uuid)
        self.identifiers.append(identifier)

    def delete(self, index):
        del self.dates[index]
        del self.types[index]
        del self.incident_uuids[index]
        del self.identifiers[index]

    def delete_by_id(self, uuid):
        ids_to_delete = list()
        for i in range(len(self.dates)):
            if self.types[i] != 'change_status' and self.incident_uuids[i] == uuid:
                ids_to_delete.append(i)
        for i in ids_to_delete:
            self.delete(i)

    def handle(self):
        if self.dates[0] < datetime.utcnow():
            type_ = self.types[0]
            incident_uuid = self.incident_uuids[0]
            identifier = self.identifiers[0]
            self.delete(0)

            return type_, incident_uuid, identifier
        return None, None, None

    def serialize(self):
        result = list()
        for i in range(len(self.dates)):
            if self.types[i] == 0:
                result.append({
                    'datetime': self.dates[i],
                    'type': Queue.TYPES[self.types[i]],
                    'incident_uuid': self.incident_uuids[i]
                })
            elif self.types[i] == 1:
                result.append({
                    'datetime': self.dates[i],
                    'type': Queue.TYPES[self.types[i]],
                    'incident_uuid': self.incident_uuids[i],
                    'step_number': self.identifiers[i]
                })
            else:
                result.append({
                    'datetime': self.dates[i],
                    'type': Queue.TYPES[self.types[i]],
                    'incident_uuid': self.incident_uuids[i],
                    'webhook': self.identifiers[i]
                })
        return result


def unix_sleep_to_timedelta(unix_sleep_time):
    value = int(unix_sleep_time[:-1])
    unit = unix_sleep_time[-1]
    unit_map = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
    return timedelta(**{unit_map[unit]: value})
