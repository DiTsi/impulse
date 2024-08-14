import os
from typing import Optional, Tuple, Dict

from app import logger
from app.incident import Incident
from app.incident.helpers import gen_uuid
from config import incidents_path


class Incidents:
    def __init__(self, incidents_list):
        self.by_uuid: Dict[str, Incident] = {gen_uuid(i.last_state.get('groupLabels')): i for i in incidents_list}

    def get(self, alert: Dict) -> Tuple[Optional[Incident], str]:
        uuid_ = gen_uuid(alert.get('groupLabels'))
        return self.by_uuid.get(uuid_), uuid_

    def get_by_ts(self, ts: str) -> Optional[Tuple[Incident, str]]:
        return next(((v, k) for k, v in self.by_uuid.items() if v.ts == ts), None)

    def add(self, incident: Incident) -> str:
        uuid_ = gen_uuid(incident.last_state.get('groupLabels'))
        self.by_uuid[uuid_] = incident
        return uuid_

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
