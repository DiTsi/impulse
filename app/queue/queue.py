from collections import namedtuple
from datetime import datetime
from threading import Lock

from app.logging import logger

QueueItem = namedtuple('QueueItem', ['datetime', 'type', 'incident_uuid', 'identifier', 'data'])


class Queue:
    __slots__ = ['items', 'lock']

    def __init__(self, check_update):
        self.items = []
        self.lock = Lock()

        if check_update:
            check_update_datetime = datetime.utcnow()
            self.put(check_update_datetime, 'check_update', None, 'first')

    def put_first(self, datetime_, type_, incident_uuid=None, identifier=None, data=None):
        new_item = QueueItem(datetime_, type_, incident_uuid, identifier, data)
        with self.lock:
            self._insert_item_first(new_item)

    def put(self, datetime_, type_, incident_uuid=None, identifier=None, data=None):
        new_item = QueueItem(datetime_, type_, incident_uuid, identifier, data)
        with self.lock:
            self._insert_item_sorted(new_item)

    def delete_by_id(self, uuid, delete_steps=True, delete_status=True):
        with self.lock:
            self._perform_delete(uuid, delete_steps, delete_status)

    def _perform_delete(self, uuid, delete_steps=True, delete_status=True):
        self.items = [
            item for item in self.items
            if not (item.incident_uuid == uuid and (
                (delete_steps and item.type == 'chain_step') or
                (delete_status and item.type == 'update_status')
            ))
        ]

    def recreate(self, status, uuid, incident_chain):
        if status != 'resolved':
            new_items = []
            for i, s in enumerate(incident_chain):
                if not s['done']:
                    new_items.append(QueueItem(s['datetime'], 'chain_step', uuid, i, None))

            with self.lock:
                for new_item in new_items:
                    self._insert_item_sorted(new_item)

    def _insert_item_sorted(self, new_item):
        for i, item in enumerate(self.items):
            if new_item.datetime < item.datetime:
                self.items.insert(i, new_item)
                return
        self.items.append(new_item)

    def _insert_item_first(self, new_item):
        self.items.insert(0, new_item)

    def update(self, uuid_, incident_status_change, status):
        with self.lock:
            if status == 'resolved':
                self._perform_delete(uuid_, delete_steps=True, delete_status=False)
            self._perform_delete(uuid_, delete_steps=False, delete_status=True)
            self._insert_item_sorted(QueueItem(incident_status_change, 'update_status', uuid_, None, None)) #!

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
        logger.info('Creating Queue')
        queue = cls(check_update)

        for uuid_, incident in incidents.by_uuid.items():
            queue.recreate(incident.status, uuid_, incident.get_chain())
            queue.put(incident.status_update_datetime, 'update_status', uuid_)

        return queue
