from app.logging import logger

actual_version = 'v0.4'


def update_incident(incident):
    logger.info(f'Update incident \'{incident.uuid}\' from version \'{incident.version}\' to \'{actual_version}\'')
    # none
    if not incident.version:
        none_to_0_4(incident)


def none_to_0_4(incident):
    incident.version = 'v0.4'
    incident.dump()
