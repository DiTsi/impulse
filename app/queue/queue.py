from collections import namedtuple
from datetime import datetime
from threading import Lock

from app.logging import logger

QueueItem = namedtuple('QueueItem', ['datetime', 'type', 'incident_uuid', 'identifier', 'data'])


class Queue:
    def __init__(self, check_update):
        self.items = []
        self.lock = Lock()

        if check_update:
            check_update_datetime = datetime.utcnow()
            self.put(check_update_datetime, 'check_update', None, 'first')

    def put(self, datetime_, type_, incident_uuid=None, identifier=None, data=None):
        new_item = QueueItem(datetime_, type_, incident_uuid, identifier, data)
        with self.lock:
            for i, item in enumerate(self.items):
                if datetime_ < item.datetime:
                    self.items.insert(i, new_item)
                    return
            self.items.append(new_item)

    def delete(self, index):
        with self.lock:
            del self.items[index]

    def delete_by_id(self, uuid, delete_steps=True, delete_status=True):
        with self.lock:
            self.items = [
                item for item in self.items
                if not (item.incident_uuid == uuid and (
                        (delete_steps and item.type == 'chain_step') or
                        (delete_status and item.type == 'update_status')
                ))
            ]

    def append(self, uuid, incident_chain):
        with self.lock:
            for i, s in enumerate(incident_chain):
                if not s['done']:
                    self.put(s['datetime'], 'chain_step', uuid, i)

    def update(self, uuid_, incident_status_change, status):
        with self.lock:
            if uuid_ not in [item.incident_uuid for item in self.items]:
                self.put(incident_status_change, 'update_status', uuid_)
            else:
                self.delete_by_id(uuid_, delete_steps=False, delete_status=True)
                self.put(incident_status_change, 'update_status', uuid_)

            if status == 'resolved':
                self.delete_by_id(uuid_, delete_steps=True, delete_status=False)

    def handle(self):
        with self.lock:
            if self.items and self.items[0].datetime < datetime.utcnow():
                item = self.items.pop(0)
                return item.type, item.incident_uuid, item.identifier, item.data
        return None, None, None, None

    def serialize(self):
        with self.lock:
            return [
                {
                    'datetime': item.datetime,
                    'type': item.type,
                    'incident_uuid': item.incident_uuid,
                    'identifier': item.identifier
                } for item in self.items
            ]

    @classmethod
    def recreate_queue(cls, incidents, check_update):
        logger.debug('Creating Queue')
        queue = cls(check_update)

        for uuid_, incident in incidents.by_uuid.items():
            queue.append(uuid_, incident.get_chain())
            queue.put(incident.status_update_datetime, 'update_status', uuid_)

        if queue.items:
            logger.debug('Queue restored with incidents')
        else:
            logger.debug('Empty Queue created')

        return queue
