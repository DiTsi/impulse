default_message_template = """
{% set status = payload.get("status", "Unknown") -%}
{% set annotations = payload.get("commonAnnotations", {}).copy() -%}
{% set commonLabels = payload.get("commonLabels", {}) -%}
{% set status_emoji = {"firing": ":fire:", "resolved": ":white_check_mark:"}[status] | default(":warning:") -%}
{{ status_emoji }} {{ commonLabels.alertname }}

{% set annotations = payload.get("commonAnnotations", {}) -%}
{% set groupLabels = payload.get("groupLabels", {}) -%}
{% set commonLabels = payload.get("commonLabels", {}) -%}
{% set severity = groupLabels.severity -%}
{% set alerts = payload.get("alerts", {}) -%}
{% set severity_emoji = {"critical": ":rotating_light:", "warning": ":warning:" }[severity] | default(":question:") -%}
**{{ annotations.summary }}**
{% if annotations.description %}_{{ annotations.description }}_{% endif -%}
{%- if alerts[0].labels.instance %}
**Instance:** {{ alerts[0].labels.instance }}  {%- for l in alerts[0].labels.keys() if l != 'alertname' and l != 'region' and l != 'instance' and l not in commonLabels.keys() -%}{{l}}=`{{ alerts[0].labels[l] }}`{% if not loop.last %},  {% endif %}{% endfor %}
{%- endif %}
{%- if annotations.value %}
**Value:** {{ annotations.value }}
{%- endif %}
{%- if commonLabels | length > 0 %}
**Labels:**
{%- for k, v in commonLabels.items() if k != 'alertname' and k != 'instance' %}
   {{ k }}=`{{ v }}`
{%- endfor %}
{%- endif %}
{% if annotations.expr %} <{% raw %}https://grafana.com/explore?orgId=1&left=%7B"datasource":"prometheus_1","queries":%5B%7B"refId":"A","datasource":%7B"type":"prometheus","uid":"prometheus_1"%7D,"editorMode":"code","expr":"{% endraw %}{{ annotations.expr | urlencode | replace('%2C',',') | replace('%5C','%5C%22') | replace('%22','%5C%22') | replace('/','%2F') | replace('%0A','') }}{% raw %}","legendFormat":"__auto","range":true,"instant":true%7D%5D,"range":%7B"from":"now-1h","to":"now"%7D%7D{% endraw %}|:grafana:>{% endif %}
"""
