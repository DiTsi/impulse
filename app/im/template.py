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
{#-   #} (<http://google.com|NotDefined>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- else -%}
{#-  -#}{%- if fields.unit.exists -%}
{#-     #} (<@{{ fields.unit.id }}>)
{#-  -#}{%- else -%}
{#      #} (<http://google.com|NotFound>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#-  -#}{%- endif -%}
{#--#}{%- endif -%}
{%- elif fields.type == 'mattermost' -%}
:bell: user **{{ fields.name -}}**
{#--#}{%- if not fields.unit -%}
{#-   #} ([NotDefined](http://google.com))  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- else -%}
{#-  -#}{%- if fields.unit.exists -%}
{#-     #} (@{{ fields.unit.username }})
{#-  -#}{%- else -%}
{#      #} ([NotFound](http://google.com))  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
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
{#-   #} (<http://google.com|NotDefined>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- else -%}
{#-   #} ({%- for u in existing_users %}<@{{ u }}>{% if not loop.last %}, {% endif %}{% endfor -%})
{#-  -#}{% if absent_users | length > 0 %}  |  {% for u in absent_users %}*{{ u }}* (<http://google.com|NotFound>){% if not loop.last %}, {% endif %}{% endfor %}{% endif %}
{#-  -#}{% if undefined_users | length > 0 %}  |  {% for u in undefined_users %}*{{ u }}* (<http://google.com|NotDefined>){% if not loop.last %}, {% endif %}{% endfor %}{% endif %}
{#-  -#}{% if absent_users | length > 0 or undefined_users | length > 0 %}  |  :loudspeaker: admins ({% for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor %}){% endif -%}
{#--#}{%- endif -%}
{%- elif fields.type == 'mattermost' -%}
{%- set existing_users = [] -%}
{%- for u in fields.unit.users if u.exists %}{% set _ = existing_users.append(u.username) %}{% endfor -%}
:bell: user_group **{{ fields.name -}}**
{#--#}{%- if not fields.unit -%}
{#-   #} ([NotDefined](http://google.com))  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- else -%}
{#-   #} ({%- for u in existing_users %}@{{ u }}{% if not loop.last %}, {% endif %}{% endfor -%})
{#-  -#}{% if absent_users | length > 0 %}  |  {% for u in absent_users %}**{{ u }}** ([NotFound](http://google.com)){% if not loop.last %}, {% endif %}{% endfor %}{% endif %}
{#-  -#}{% if undefined_users | length > 0 %}  |  {% for u in undefined_users %}**{{ u }}** ([NotDefined](http://google.com)){% if not loop.last %}, {% endif %}{% endfor %}{% endif %}
{#-  -#}{% if absent_users | length > 0 or undefined_users | length > 0 %}  |  :bell: admins ({% for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor %}){% endif -%}
{#--#}{%- endif -%}
{%- endif -%}
"""

update_status = """
{%- if fields.type == 'slack' -%}
update: status *{{ fields.status -}}*
{#--#}{%- if fields.status == 'unknown' -%}
{#-   #}  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- endif -%}
{%- elif fields.type == 'mattermost' -%}
update: status **{{ fields.status -}}**
{#--#}{%- if fields.status == 'unknown' -%}
{#-   #}  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
{#--#}{%- endif -%}
{%- endif -%}
"""

# notification_webhook = """
# :loudspeaker: webhook *{{ fields.webhook_name }}* {% if fields.id is not none -%}
#     (<@{{ fields.id }}>)
# {%- else %} (<http://google.com|NF>)  |  :loudspeaker: admins (
# {%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor %})
# {%- endif %}
# {% elif fields.type == 'mattermost' %}
# :loud_sound: webhook **{{ fields.webhook_name }}** {% if fields.id is not none -%}
#     (<@{{ fields.id }}>)
# {%- else %} (<http://google.com|NF>)  |  :loud_sound: admins (
# {%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor %})
# {%- endif %}
# """
