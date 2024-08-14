import os

from app import logger
from app.incident.helpers import gen_uuid
from config import incidents_path


class Incidents:
    def __init__(self, incidents_list):
        self.by_uuid = {gen_uuid(i.last_state.get('groupLabels')): i for i in incidents_list}

    def get(self, alert):
        uuid_ = gen_uuid(alert.get('groupLabels'))
        incident = self.by_uuid.get(uuid_)
        return incident, uuid_

    def get_by_ts(self, ts):  # !
        for k, v in self.by_uuid.items():
            if v.ts == ts:
                return v, k
        return None

    def add(self, incident):
        uuid_ = gen_uuid(incident.last_state.get('groupLabels'))
        self.by_uuid[uuid_] = incident
        return uuid_

    def del_by_uuid(self, uuid_):
        incident = self.by_uuid[uuid_]
        link = incident.link
        del self.by_uuid[uuid_]
        os.remove(f'{incidents_path}/{uuid_}.yml')
        logger.info(f'Incident \'{uuid_}\' closed. Link: {link}')

    def serialize(self):
        r = {str(k): self.by_uuid[k].serialize() for k in self.by_uuid.keys()}
        return r
