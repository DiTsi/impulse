from jinja2 import Template

from app.logger import logger


class MessageTemplate:
    def __init__(self, name, text):
        self.name = name
        self.text = text

    def __repr__(self):
        return self.name

    def form_message(self, alert_state):
        template = Template(self.text)
        return template.render(payload=alert_state)


def generate_message_templates(message_templates_dict):
    logger.debug(f'Creating MessageTemplates')
    message_templates = {
        name: MessageTemplate(
            name,
            message_templates_dict[name]['text']
        ) for name in message_templates_dict.keys()
    }
    logger.debug(f'MessageTemplates created')
    return message_templates
