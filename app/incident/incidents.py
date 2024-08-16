import os
from typing import Dict

from app import logger
from app.incident import Incident
from app.incident.helpers import gen_uuid
from config import incidents_path


class Incidents:
    def __init__(self, incidents_list):
        self.by_uuid: Dict[str, Incident] = {i.uuid: i for i in incidents_list}

    def get(self, alert: Dict) -> Incident | None:
        uuid_ = gen_uuid(alert.get('groupLabels'))
        return self.by_uuid.get(uuid_)

    def get_by_ts(self, ts: str) -> Incident | None:
        return next((incident for incident in self.by_uuid.values() if incident.ts == ts), None)

    def add(self, incident: Incident):
        self.by_uuid[incident.uuid] = incident

    def del_by_uuid(self, uuid_: str):
        incident = self.by_uuid.pop(uuid_, None)
        if incident:
            try:
                os.remove(f'{incidents_path}/{uuid_}.yml')
                logger.info(f'Incident \'{uuid_}\' closed. Link: {incident.link}')
            except FileNotFoundError:
                logger.error(f'Failed to delete incident file for uuid: {uuid_}. File not found.')
        else:
            logger.warning(f'Incident with uuid: {uuid_} not found in the collection.')

    def serialize(self) -> Dict[str, Dict]:
        return {uuid_: incident.serialize() for uuid_, incident in self.by_uuid.items()}
