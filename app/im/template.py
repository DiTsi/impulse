from jinja2 import Template

from app.incident.incident import Incident


class JinjaTemplate:
    def __init__(self, template):
        self.template = template

    def form_message(self, alert_state, incident: Incident = None):
        template = Template(self.template)
        incident_data = incident.serialize() if incident else {}
        return template.render(payload=alert_state, incident=incident_data)

    def form_notification(self, fields):
        template = Template(self.template)
        return template.render(fields=fields)


notification_user = """
{%- if fields.type == 'slack' -%}
:loudspeaker: user *{{ fields.name -}}*
{#--#}{%- if not fields.unit -%}
{#-   #} (<https://docs.impulse.bot/latest/warnings/NotDefined/|NotDefined>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- else -%}
{#-  -#}{%- if fields.unit.exists -%}
{#-     #} (<@{{ fields.unit.id }}>)
{#-  -#}{%- else -%}
{#      #} (<https://docs.impulse.bot/latest/warnings/NotFound/|NotFound>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#-  -#}{%- endif -%}
{#--#}{%- endif -%}
{%- elif fields.type == 'mattermost' -%}
:bell: user **{{ fields.name -}}**
{#--#}{%- if not fields.unit -%}
{#-   #} ([NotDefined](https://docs.impulse.bot/latest/warnings/NotDefined/))  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- else -%}
{#-  -#}{%- if fields.unit.exists -%}
{#-     #} (@{{ fields.unit.username }})
{#-  -#}{%- else -%}
{#      #} ([NotFound](https://docs.impulse.bot/latest/warnings/NotFound/))  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
{#-  -#}{%- endif -%}
{#--#}{%- endif -%}
{%- endif -%}
"""

notification_user_group = """
{%- set undefined_users = [] -%}
{%- for u in fields.unit.users if not u.defined %}{% set _ = undefined_users.append(u.name) %}{% endfor -%}
{%- set absent_users = [] -%}
{%- for u in fields.unit.users if u.defined and not u.exists %}{% set _ = absent_users.append(u.name) %}{% endfor -%}
{%- if fields.type == 'slack' -%}
{%- set existing_users = [] -%}
{%- for u in fields.unit.users if u.exists %}{% set _ = existing_users.append(u.id) %}{% endfor -%}
:loudspeaker: user_group *{{ fields.name -}}*
{#--#}{%- if not fields.unit -%}
{#-   #} (<https://docs.impulse.bot/latest/warnings/NotDefined/|NotDefined>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- else -%}
{#-   #} ({%- for u in existing_users %}<@{{ u }}>{% if not loop.last %}, {% endif %}{% endfor -%})
{#-  -#}{% if absent_users | length > 0 %}  |  {% for u in absent_users %}*{{ u }}* (<https://docs.impulse.bot/latest/warnings/NotFound/|NotFound>){% if not loop.last %}, {% endif %}{% endfor %}{% endif %}
{#-  -#}{% if undefined_users | length > 0 %}  |  {% for u in undefined_users %}*{{ u }}* (<https://docs.impulse.bot/latest/warnings/NotDefined/|NotDefined>){% if not loop.last %}, {% endif %}{% endfor %}{% endif %}
{#-  -#}{% if absent_users | length > 0 or undefined_users | length > 0 %}  |  :loudspeaker: admins ({% for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor %}){% endif -%}
{#--#}{%- endif -%}
{%- elif fields.type == 'mattermost' -%}
{%- set existing_users = [] -%}
{%- for u in fields.unit.users if u.exists %}{% set _ = existing_users.append(u.username) %}{% endfor -%}
:bell: user_group **{{ fields.name -}}**
{#--#}{%- if not fields.unit -%}
{#-   #} ([NotDefined](https://docs.impulse.bot/latest/warnings/NotDefined/))  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- else -%}
{#-   #} ({%- for u in existing_users %}@{{ u }}{% if not loop.last %}, {% endif %}{% endfor -%})
{#-  -#}{% if absent_users | length > 0 %}  |  {% for u in absent_users %}**{{ u }}** ([NotFound](https://docs.impulse.bot/latest/warnings/NotFound/)){% if not loop.last %}, {% endif %}{% endfor %}{% endif %}
{#-  -#}{% if undefined_users | length > 0 %}  |  {% for u in undefined_users %}**{{ u }}** ([NotDefined](https://docs.impulse.bot/latest/warnings/NotDefined/)){% if not loop.last %}, {% endif %}{% endfor %}{% endif %}
{#-  -#}{% if absent_users | length > 0 or undefined_users | length > 0 %}  |  :bell: admins ({% for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor %}){% endif -%}
{#--#}{%- endif -%}
{%- endif -%}
"""

update_status = """
{%- if fields.type == 'slack' -%}
update: status *{% if fields.status == 'unknown' %}<https://docs.impulse.bot/latest/warnings/StatusUnknown/|unknown>{% else %}{{ fields.status }}{% endif %}*
{#--#}{%- if fields.status == 'unknown' -%}
{#-   #}  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- endif -%}
{%- elif fields.type == 'mattermost' -%}
update: status **{% if fields.status == 'unknown' %}[unknown](https://docs.impulse.bot/latest/warnings/StatusUnknown/){% else %}{{ fields.status }}{% endif %}**
{#--#}{%- if fields.status == 'unknown' -%}
{#-   #}  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- endif -%}
{%- endif -%}
"""

update_alerts = """
{%- if fields.type == 'slack' -%}
update: {% if fields.firing %}new alerts *firing*{% if fields.recreate %}  |  restart chain{% endif %}{% else %}some alerts *resolved*{% endif %}
{%- elif fields.type == 'mattermost' -%}
update: {% if fields.firing %}new alerts **firing**{% if fields.recreate %}  |  restart chain{% endif %}{% else %}some alerts **resolved**{% endif %}
{%- endif -%}
"""

notification_webhook = """
{%- if fields.type == 'slack' -%}
:loudspeaker: webhook *{{ fields.name -}}*
{#--#}{%- if fields.unit is none -%}
{#-   #} (<https://docs.impulse.bot/latest/warnings/NotDefined/|NotDefined>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- else -%}
{#-  -#}{%- if fields.result == 'ok' -%}
{#-     #} ({% if fields.response < 400 %}{{ fields.response }}{% else %}<https://docs.impulse.bot/latest/warnings/ResponseCode/|{{ fields.response }}>{% endif %})
{#-  -#}{%- elif fields.result == 'Timeout' -%}
{#      #} (<https://docs.impulse.bot/latest/warnings/TimeoutError/|TimeoutError>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#-  -#}{%- else -%}
{#      #} (<https://docs.impulse.bot/latest/warnings/ConnectionError/|ConnectionError>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#-  -#}{%- endif -%}
{#--#}{%- endif -%}
{%- elif fields.type == 'mattermost' -%}
:bell: webhook **{{ fields.name -}}**
{#--#}{%- if fields.unit is none -%}
{#-   #} ([NotDefined](https://docs.impulse.bot/latest/warnings/NotDefined/))  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- else -%}
{#-  -#}{%- if fields.result == 'ok' -%}
{#-     #} ({% if fields.response < 400 %}{{ fields.response }}{% else %}[{{ fields.response }}](https://docs.impulse.bot/latest/warnings/ResponseCode/){% endif %})
{#-  -#}{%- elif fields.result == 'Timeout' -%}
{#      #} ([TimeoutError](https://docs.impulse.bot/latest/warnings/TimeoutError/))  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
{#-  -#}{%- else -%}
{#      #} ([ConnectionError](https://docs.impulse.bot/latest/warnings/ConnectionError/))  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
{#-  -#}{%- endif -%}
{#--#}{%- endif -%}
{%- endif -%}
"""
