from jinja2 import Template

from app.im.mattermost.templates import mattermost_incident_body_template, mattermost_incident_header_template, \
    mattermost_incident_status_icons_template
from app.im.slack.templates import slack_incident_body_template, slack_incident_header_template, \
    slack_incident_status_icons_template
from app.logging import logger


class MessageTemplate:
    def __init__(self, template):
        self.template = template

    def form_message(self, alert_state):
        template = Template(self.template)
        return template.render(payload=alert_state)


def generate_template(type_, body_dict=None, header_dict=None, status_icons_dict=None):
    if type_ == 'slack':
        if body_dict is not None:
            incident_body = MessageTemplate(body_dict)
        else:
            logger.debug(f'No application.templates.body defined in impulse.yml. Continue with default')
            incident_body = MessageTemplate(slack_incident_body_template)

        if header_dict is not None:
            incident_header = MessageTemplate(header_dict)
        else:
            logger.debug(f'No application.templates.header defined in impulse.yml. Continue with default')
            incident_header = MessageTemplate(slack_incident_header_template)

        if status_icons_dict is not None:
            incident_status_icons = MessageTemplate(status_icons_dict)
        else:
            logger.debug(f'No application.templates.status_icons defined in impulse.yml. Continue with default')
            incident_status_icons = MessageTemplate(slack_incident_status_icons_template)
    else:
        if body_dict is not None:
            incident_body = MessageTemplate(body_dict)
        else:
            logger.debug(f'No application.templates.body defined in impulse.yml. Continue with default')
            incident_body = MessageTemplate(mattermost_incident_body_template)

        if header_dict is not None:
            incident_header = MessageTemplate(header_dict)
        else:
            logger.debug(f'No application.templates.header defined in impulse.yml. Continue with default')
            incident_header = MessageTemplate(mattermost_incident_header_template)

        if status_icons_dict is not None:
            incident_status_icons = MessageTemplate(status_icons_dict)
        else:
            logger.debug(f'No application.templates.status_icons defined in impulse.yml. Continue with default')
            incident_status_icons = MessageTemplate(mattermost_incident_status_icons_template)
    return incident_body, incident_header, incident_status_icons
