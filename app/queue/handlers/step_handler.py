from app.logging import logger
from app.queue.handlers.base_handler import BaseHandler


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
            text = f'➤ webhook {self.app.format_text_bold(webhook_name)}: '
            if webhook:
                r_code = webhook.push()
                incident.chain_update(identifier, done=True, result=r_code)
                text += f'{r_code}'
                admins_text = self.app.get_admins_text()
                text += f'\n➤ admins: {admins_text}'
                _ = self.app.post_thread(incident.channel_id, incident.ts, text)
                incident.chain_update(identifier, done=True, result=None)
                if r_code >= 400:
                    logger.warning(f'Webhook \'{webhook_name}\' response code is {r_code}')
            else:
                admins_text = self.app.get_admins_text()
                text += (f'{self.app.format_text_bold("not found in `impulse.yml`")}\n'
                         f'➤ {admins_text}')
                _ = self.app.post_thread(incident.channel_id, incident.ts, text)
                logger.warning(f'Webhook \'{webhook_name}\' not found in impulse.yml')
                incident.chain_update(identifier, done=True, result=None)
        else:
            r_code = self.app.notify(incident, step['type'], step['identifier'])
            incident.chain_update(identifier, done=True, result=r_code)
