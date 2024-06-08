from jinja2 import Template

from app.logger import logger


class MessageTemplate:
    def __init__(self, template):
        self.template = template

    def form_message(self, alert_state):
        template = Template(self.template)
        return template.render(payload=alert_state)


def generate_message_template(message_template_dict):
    logger.debug(f'Creating MessageTemplate')

    message_template = MessageTemplate(
        message_template_dict
    )
    logger.debug(f'MessageTemplate created')
    return message_template
