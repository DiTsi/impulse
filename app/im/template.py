from jinja2 import Template


class JinjaTemplate:
    def __init__(self, template):
        self.template = template

    def form_message(self, alert_state):
        template = Template(self.template)
        return template.render(payload=alert_state)


def generate_template(type_, body_dict=None, header_dict=None, status_icons_dict=None):
    if type_ == 'slack':
        incident_body = JinjaTemplate(body_dict)
        incident_header = JinjaTemplate(header_dict)
        incident_status_icons = JinjaTemplate(status_icons_dict)
    else:
        incident_body = JinjaTemplate(body_dict)
        incident_header = JinjaTemplate(header_dict)
        incident_status_icons = JinjaTemplate(status_icons_dict)
    return incident_body, incident_header, incident_status_icons
