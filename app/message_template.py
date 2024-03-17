from jinja2 import Template


class MessageTemplate:
    def __init__(self, name, text):
        self.name = name
        self.text = text

    def __repr__(self):
        return self.name

    def form_message(self, alert_state):
        template = Template(self.text)
        return template.render(payload=alert_state)
