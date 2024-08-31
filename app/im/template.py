from jinja2 import Template

from app.incident.incident import Incident


class JinjaTemplate:
    def __init__(self, template):
        self.template = template

    def form_message(self, alert_state, incident: Incident = None):
        template = Template(self.template)
        incident_data = incident.serialize() if incident else {}
        return template.render(payload=alert_state, incident=incident_data)


def generate_template(body_dict=None, header_dict=None, status_icons_dict=None):
    incident_body = JinjaTemplate(body_dict)
    incident_header = JinjaTemplate(header_dict)
    incident_status_icons = JinjaTemplate(status_icons_dict)
    return incident_body, incident_header, incident_status_icons
