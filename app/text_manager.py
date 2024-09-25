from dataclasses import field, dataclass


class TextTemplate:
    def __init__(self, template):
        self.template = template

    def __call__(self, **kwargs):
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required argument '{e.args[0]}' for template: '{self.template}'")

    def __str__(self):
        return self.template


@dataclass
class TextManager:
    templates: dict = field(default_factory=dict, init=False)
    _instance: 'TextManager' = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.templates = {
            'notify_message': "{header}\n{unit_text}",
            'webhook_name': "➤ webhook {webhook_name}: ",
            'notify_webhook_message': "{header}\n{notification_text}",
            'admins': "\n➤ admins: {admins}",
            'status_update': "{header}\n➤ status: {status}",
            'unknown_status': "{header}\n➤ status: {status}\n➤ admins: {admins}",
            'new_version': "{new_version} {changelog_link}\n\n{release_notes}",
            'unit_not_defined': "➤ {unit_type} {identifier}: not defined in impulse.yml\n➤ admins: {admins}",
        }
        self._initialize_templates()

    def _initialize_templates(self):
        for key, template in self.templates.items():
            setattr(self, key, TextTemplate(template))

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_template(cls, name, **kwargs):
        instance = cls.get_instance()
        if name in instance.templates:
            return getattr(instance, name)(**kwargs)
        else:
            raise ValueError(f"Template '{name}' does not exist.")
