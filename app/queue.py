from datetime import datetime, timedelta

from app.logging import logger
from .im import slack_env, slack_admins_template_string, mattermost_env, mattermost_admins_template_string
from .update import get_latest_tag


class Queue:
    def __init__(self, check_update):
        self.dates = []
        self.types = []
        self.incident_uuids = []
        self.identifiers = []
        self.lock = False

        if check_update:
            check_update_datetime = datetime.utcnow()
            self.put(check_update_datetime, 'check_update', None, 'first')

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
            elif self.types[i] == 'check_update':
                result.append({
                    'datetime': self.dates[i],
                    'type': self.types[i]
                })
        return result


def queue_handle(incidents, queue_, application, webhooks, latest_tag):
    if len(queue_.dates) == 0:
        return
    type_, uuid_, identifier = queue_.handle()
    if type_ is not None:
        if type_ == 'update_status':
            queue_handle_status_update(incidents, uuid_, queue_, application)
        elif type_ == 'chain_step':
            queue_handle_step(incidents, uuid_, application, identifier, webhooks)
        elif type_ == 'check_update':
            queue_handle_check_update(identifier, queue_, application, latest_tag)


def queue_handle_check_update(identifier, queue_, application, latest_tag):
    current_tag = get_latest_tag()
    if identifier == 'first':
        latest_tag['version'] = current_tag
    else:
        current_tag = 'v0.4' #!
        if current_tag != latest_tag['version']:
            application.new_version_notification(application.default_channel_id, current_tag)
            latest_tag['version'] = current_tag
    queue_.put(datetime.utcnow() + timedelta(seconds=10), 'check_update', None, identifier=None)


def queue_handle_step(incidents, uuid_, application, identifier, webhooks):
    incident_ = incidents.by_uuid[uuid_]
    step = incident_.chain[identifier]
    if step['type'] == 'webhook':
        webhook_name = step['identifier']
        webhook = webhooks.get(webhook_name)
        if application.type == 'slack':
            admins = [a.slack_id for a in application.admin_users]
        else:
            admins = [a.username for a in application.admin_users]
        text = f'notify webhook *{webhook_name}*'
        if webhook:
            r_code = webhook.push()
            incident_.chain_update(uuid_, identifier, done=True, result=r_code)
            if r_code >= 300:
                if application.type == 'slack':
                    admins_text = slack_env.from_string(slack_admins_template_string).render(users=admins)
                    text += (f'\n>_response code: {r_code}_'
                             f'\n>_{admins_text}_')
                else:
                    admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(users=admins)
                    text += (f'\n|_response code: {r_code}_'
                             f'\n|_{admins_text}_')
                _ = application.post_thread(incident_.channel_id, incident_.ts, text)
                logger.warning(f'Webhook \'{webhook_name}\' response code is {r_code}')
                incident_.chain_update(uuid_, identifier, done=True, result=None)
        else:
            if application.type == 'slack':
                admins_text = slack_env.from_string(slack_admins_template_string).render(users=admins)
                text += (f'\n>_not found in `impulse.yml`_'
                         f'\n>_{admins_text}_')
            else:
                admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(users=admins)
                text += (f'\n|_not found in `impulse.yml`_'
                         f'\n|_{admins_text}_')
            _ = application.post_thread(incident_.channel_id, incident_.ts, text)
            logger.warning(f'Webhook \'{webhook_name}\' not found in impulse.yml')
            incident_.chain_update(uuid_, identifier, done=True, result=None)
    else:
        r_code = application.notify(incident_, step['type'], step['identifier'])
        incident_.chain_update(uuid_, identifier, done=True, result=r_code)


def queue_handle_status_update(incidents, uuid, queue_, application):
    incident_ = incidents.by_uuid[uuid]
    status_updated = incident_.set_next_status()
    application.update(
        uuid, incident_, incident_.status, incident_.last_state, status_updated,
        incident_.chain_enabled, incident_.status_enabled
    )
    if incident_.status == 'closed':
        incidents.del_by_uuid(uuid)
        queue_.delete_by_id(uuid)
    elif incident_.status == 'unknown':
        queue_.update(uuid, incident_.status_update_datetime, incident_.status)


def recreate_queue(incidents, check_update):
    logger.debug(f'Creating Queue')
    queue_ = Queue(check_update)
    if bool(incidents.by_uuid):
        for uuid_, i in incidents.by_uuid.items():
            queue_.append(uuid_, i.get_chain())
            queue_.put(i.status_update_datetime, 'update_status', uuid_)
        logger.debug(f'Queue restored')
    else:
        logger.debug(f'Empty Queue created')
    return queue_
