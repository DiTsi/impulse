from jinja2 import Template

from app.logging import logger
from app.application.mattermost.message_template import default_message_template as mattermost_default_message_template
from app.application.slack.message_template import default_message_template as slack_default_message_template


class MessageTemplate:
    def __init__(self, template):
        self.template = template

    def form_message(self, alert_state):
        template = Template(self.template)
        return template.render(payload=alert_state)


def generate_message_template(type, message_template_dict=None):
    if message_template_dict:
        message_template = MessageTemplate(message_template_dict)
    else:
        logger.debug(f'No message_template defined in impulse.yml. Continue with default')
        if type == 'slack':
            message_template = MessageTemplate(slack_default_message_template)
        else:
            message_template = MessageTemplate(mattermost_default_message_template)
    return message_template
