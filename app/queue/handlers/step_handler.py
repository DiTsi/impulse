from app.logging import logger
from app.queue.handlers.base_handler import BaseHandler
from app.text_manager import TextManager


class StepHandler(BaseHandler):
    """
    StepHandler class is responsible for handling the step event.

    :param queue: Queue instance
    :param application: Application instance
    :param incidents: Incidents instance
    :param webhooks: Webhooks instance
    """
    __slots__ = ['queue', 'application', 'incidents', 'webhooks']

    def __init__(self, queue, application, incidents, webhooks):
        super().__init__(queue, application, incidents)
        self.webhooks = webhooks

    def handle(self, uuid_, identifier):
        incident = self.incidents.by_uuid[uuid_]
        step = incident.chain[identifier]
        if step['type'] == 'webhook':
            webhook_name = step['identifier']
            webhook = self.webhooks.get(webhook_name)
            text = TextManager.get_template(
                'webhook_name',
                webhook_name=self.app.format_text_bold(webhook_name)
            )
            if webhook is not None:
                result, r_code = webhook.push()
                self.app.notify_webhook(incident, text, result, response_code=r_code)
                incident.chain_update(identifier, done=True, result=r_code)
                logger.info(f'Incident {incident.uuid} -> chain step webhook \'{webhook_name}\': {result}, response code {r_code}')
            else:
                self.app.notify_webhook(incident, text, 'not found in impulse.yml')
                logger.warning(f'Incident {incident.uuid} -> chain step webhook \'{webhook_name}\': undefined in impulse.yml')
                incident.chain_update(identifier, done=True, result=None)
        else:
            r_code = self.app.notify(incident, step['type'], step['identifier'])
            incident.chain_update(identifier, done=True, result=r_code)
