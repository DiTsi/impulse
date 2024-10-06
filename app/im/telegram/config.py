from jinja2 import Environment

telegram_env = Environment()

telegram_admins_template_string = "{{ users | join(', ') }}"
