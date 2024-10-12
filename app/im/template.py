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

# notification_user_group = """
# {%- if fields.type == 'slack' -%}
# :loudspeaker: user *{{ fields.name -}}*
# {#--#}{%- if not fields.unit -%}
# {#-   #} (<http://google.com|NotDefined>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
# {#--#}{%- else -%}
# {#-  -#}{%- if fields.unit.exists -%}
# {#-     #} (<@{{ fields.unit.id }}>)
# {#-  -#}{%- else -%}
# {#      #} (<http://google.com|NotFound>)  |  :loudspeaker: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
# {#-  -#}{%- endif -%}
# {#--#}{%- endif -%}
# {%- elif fields.type == 'mattermost' -%}
# :bell: user **{{ fields.name -}}**
# {#--#}{%- if not fields.unit -%}
# {#-   #} (<http://google.com|NotDefined>)  |  :bell: admins ({%- for a in fields.admins %}<@{{ a }}>{% if not loop.last %},{% endif %}{% endfor -%})
# {#--#}{%- else -%}
# {#-  -#}{%- if fields.unit.exists -%}
# {#-     #} (@{{ fields.unit.username }})
# {#-  -#}{%- else -%}
# {#      #} (<http://google.com|NotFound>)  |  :bell: admins ({%- for a in fields.admins %}@{{ a }}{% if not loop.last %},{% endif %}{% endfor -%})
# {#-  -#}{%- endif -%}
# {#--#}{%- endif -%}
# {%- endif -%}
# """

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
