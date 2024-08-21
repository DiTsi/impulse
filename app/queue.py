from collections import namedtuple
from datetime import datetime, timedelta
from threading import Lock

from app.logging import logger
from app.update import get_latest_tag

QueueItem = namedtuple('QueueItem', ['datetime', 'type', 'incident_uuid', 'identifier'])


class Queue:
    def __init__(self, check_update):
        self.items = []
        self.lock = Lock()

        if check_update:
            check_update_datetime = datetime.utcnow()
            self.put(check_update_datetime, 'check_update', None, 'first')

    def put(self, datetime_, type_, incident_uuid=None, identifier=None):
        new_item = QueueItem(datetime_, type_, incident_uuid, identifier)
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
                return item.type, item.incident_uuid, item.identifier
        return None, None, None

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


def queue_handle(incidents, queue, application, webhooks, latest_tag):
    if not queue.items:
        return

    type_, uuid_, identifier = queue.handle()
    if type_ is None:
        return

    if type_ == 'update_status':
        queue_handle_status_update(incidents, uuid_, queue, application)
    elif type_ == 'chain_step':
        queue_handle_step(incidents, uuid_, application, identifier, webhooks)
    elif type_ == 'check_update':
        queue_handle_check_update(identifier, queue, application, latest_tag)


def queue_handle_check_update(identifier, queue, application, latest_tag):
    current_tag = get_latest_tag()
    if identifier != 'first' and current_tag != latest_tag['version']:
        application.new_version_notification(application.default_channel_id, current_tag)
        latest_tag['version'] = current_tag

    # Always schedule the next check update
    queue.put(datetime.utcnow() + timedelta(days=1), 'check_update', None, identifier=None)


def queue_handle_step(incidents, uuid_, application, identifier, webhooks):
    incident_ = incidents.by_uuid[uuid_]
    step = incident_.chain[identifier]
    if step['type'] == 'webhook':
        webhook_name = step['identifier']
        webhook = webhooks.get(webhook_name)
        text = f'➤ webhook {application.format_text_bold(webhook_name)}: '
        if webhook:
            r_code = webhook.push()
            incident_.chain_update(identifier, done=True, result=r_code)
            text += f'{r_code}'
            admins_text = application.get_admins_text()
            text += f'\n➤ admins: {admins_text}'
            _ = application.post_thread(incident_.channel_id, incident_.ts, text)
            incident_.chain_update(identifier, done=True, result=None)
            if r_code >= 400:
                logger.warning(f'Webhook \'{webhook_name}\' response code is {r_code}')
        else:
            admins_text = application.get_admins_text()
            text += (f'{application.format_text_bold("not found in `impulse.yml`")}\n'
                     f'➤ {admins_text}')
            _ = application.post_thread(incident_.channel_id, incident_.ts, text)
            logger.warning(f'Webhook \'{webhook_name}\' not found in impulse.yml')
            incident_.chain_update(identifier, done=True, result=None)
    else:
        r_code = application.notify(incident_, step['type'], step['identifier'])
        incident_.chain_update(identifier, done=True, result=r_code)


def queue_handle_status_update(incidents, uuid, queue, application):
    incident_ = incidents.by_uuid[uuid]
    status_updated = incident_.set_next_status()

    application.update(
        uuid, incident_, incident_.status, incident_.last_state,
        status_updated, incident_.chain_enabled, incident_.status_enabled
    )

    if incident_.status == 'closed':
        incidents.del_by_uuid(uuid)
        queue.delete_by_id(uuid)
    elif incident_.status == 'unknown':
        queue.update(uuid, incident_.status_update_datetime, incident_.status)


def recreate_queue(incidents, check_update):
    logger.debug('Creating Queue')
    queue = Queue(check_update)

    for uuid_, incident in incidents.by_uuid.items():
        queue.append(uuid_, incident.get_chain())
        queue.put(incident.status_update_datetime, 'update_status', uuid_)

    if queue.items:
        logger.debug('Queue restored with incidents')
    else:
        logger.debug('Empty Queue created')

    return queue
