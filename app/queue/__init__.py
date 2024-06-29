from datetime import datetime, timedelta


class Queue:
    # TYPES = [
    #     'update_status',
    #     'chain_step'
    #     'admin_warning'  # types: 'status_unknown', 'user_not_found', 'user_not_found_in_group', 'webhook_not_found'
    # ]

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

    def delete_by_id(self, uuid, delete_steps=True, delete_status=True):
        self.lock = True
        ids_to_delete = list()
        for i in range(len(self.dates)):
            if self.incident_uuids[i] == uuid:
                if delete_steps and self.types[i] == 'chain_step':
                    ids_to_delete.append(i)
                if delete_status and self.types[i] == 'update_status':
                    ids_to_delete.append(i)
        for i in ids_to_delete:
            self.delete(i)
        self.lock = False

    def append(self, uuid, incident_chain):
        self.lock = True
        for i in range(len(incident_chain)):
            s = incident_chain[i]
            if not s['done']:
                self.put(s['datetime'], 'chain_step', uuid, i)
        self.lock = False

    def update(self, uuid_, incident_status_change, status):
        self.lock = True
        if uuid_ not in self.incident_uuids:
            self.put(incident_status_change, 'update_status', uuid_)
        else:
            self.delete_by_id(uuid_, delete_steps=False, delete_status=True)
            self.put(incident_status_change, 'update_status', uuid_)
        if status == 'resolved':
            self.delete_by_id(uuid_, delete_steps=True, delete_status=False)
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
            if self.types[i] == 'update_status':
                result.append({
                    'datetime': self.dates[i],
                    'type': self.types[i],
                    'incident_uuid': self.incident_uuids[i]
                })
            elif self.types[i] == 'chain_step':
                result.append({
                    'datetime': self.dates[i],
                    'type': self.types[i],
                    'incident_uuid': self.incident_uuids[i],
                    'step_number': self.identifiers[i]
                })
            elif self.types[i] == 'admin_warning':
                result.append({
                    'datetime': self.dates[i],
                    'type': self.types[i],
                    'incident_uuid': self.incident_uuids[i],
                    'admin_warning': self.identifiers[i]
                })
        return result


def unix_sleep_to_timedelta(unix_sleep_time):
    if not unix_sleep_time:
        pass
    value = int(unix_sleep_time[:-1])
    unit = unix_sleep_time[-1]
    unit_map = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
    return timedelta(**{unit_map[unit]: value})
