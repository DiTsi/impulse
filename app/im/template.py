from jinja2 import Template

from app.im.mattermost.templates import mattermost_incident_body_template
from app.im.slack.templates import slack_incident_body_template, slack_incident_header_template
from app.logging import logger


class MessageTemplate:
    def __init__(self, template):
        self.template = template

    def form_message(self, alert_state):
        template = Template(self.template)
        return template.render(payload=alert_state)


def generate_template(type, body_dict=None, header_dict=None):
    if body_dict and header_dict:
        incident_body = MessageTemplate(body_dict)
        incident_header = MessageTemplate(header_dict)
    else:
        logger.debug(f'No incident_body_template defined in impulse.yml. Continue with default')
        if type == 'slack':
            incident_body = MessageTemplate(slack_incident_body_template)
            incident_header = MessageTemplate(slack_incident_header_template)
        else:
            incident_body = MessageTemplate(mattermost_incident_body_template)
    return incident_body, incident_header
