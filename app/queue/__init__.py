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
        self.lock = False

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
        self.lock = True
        del self.dates[index]
        del self.types[index]
        del self.incident_uuids[index]
        del self.identifiers[index]
        self.lock = False

    def delete_by_id(self, uuid):
        self.lock = True
        ids_to_delete = list()
        for i in range(len(self.dates)):
            if self.incident_uuids[i] == uuid:
                ids_to_delete.append(i)
        for i in ids_to_delete:
            self.delete(i)
        self.lock = False

    def delete_steps_by_id(self, uuid):
        self.lock = True
        ids_to_delete = list()
        for i in reversed(range(len(self.dates))):
            if self.types[i] != 0 and self.incident_uuids[i] == uuid:
                ids_to_delete.append(i)
        for i in ids_to_delete:
            self.delete(i)
        self.lock = False

    def append(self, uuid, incident_chain):
        self.lock = True
        for i in range(len(incident_chain)):
            s = incident_chain[i]
            if not s['done']:
                self.put(s['datetime'], 1, uuid, i)
        self.lock = False

    def update(self, uuid_, incident_status_change, status):
        self.lock = True
        if uuid_ not in self.incident_uuids:
            self.put(incident_status_change, 0, uuid_)
        else:
            for i in range(len(self.dates)):
                incident_uuid = self.incident_uuids[i]
                type_ = self.types[i]
                if incident_uuid == uuid_ and type_ == 0:
                    self.dates[i] = incident_status_change
                    break
        if status == 'resolved':
            self.delete_steps_by_id(uuid_)
        self.lock = False

    def handle(self):
        if not self.lock:
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
    if unix_sleep_time is None:
        pass
    value = int(unix_sleep_time[:-1])
    unit = unix_sleep_time[-1]
    unit_map = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
    return timedelta(**{unit_map[unit]: value})
