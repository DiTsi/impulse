from dataclasses import field, dataclass


class TextTemplate:
    def __init__(self, template):
        self.template = template

    def __call__(self, *args):
        try:
            return self.template.format(*args)
        except IndexError as e:
            raise ValueError(f"Missing required argument for template: '{self.template}'")

    def __str__(self):
        return self.template


@dataclass
class TextManager:
    templates: dict = field(default_factory=dict, init=False)
    _instance: 'TextManager' = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.templates = {
            'user_notification': "{}\n{}",
            'group_notification': "{}\n{}",
            'status_update': "{}\n➤ status: {}",
            'unknown_status': "{}\n➤ status: {}\n➤ admins: {}",
            'new_version': "{} {}\n\n{}",
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
    def get_template(cls, name, *args):
        instance = cls.get_instance()
        if name in instance.templates:
            return getattr(instance, name)(*args)
        else:
            raise ValueError(f"Template '{name}' does not exist.")
