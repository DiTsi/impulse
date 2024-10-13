from jinja2 import Environment

telegram_env = Environment()
# TODO: Add the correct template string to include `@` before each username
telegram_admins_template_string = "{{ users | join(', ') }}"
