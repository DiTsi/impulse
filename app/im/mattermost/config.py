from jinja2 import Environment

from config import mattermost_access_token

mattermost_headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {mattermost_access_token}',
}
buttons = {
    # styles: good, warning, danger, default, primary, and success
    'chain': {
        'enabled': {
            'text': ':black_square_for_stop: Chain',
            'style': 'good'
        },
        'disabled': {
            'text': ':arrow_forward: Chain',
            'style': 'danger'
        }
    },
    'status': {
        'enabled': {
            'text': ':black_square_for_stop: Status',
            'style': 'good'
        },
        'disabled': {
            'text': ':arrow_forward: Status',
            'style': 'danger'
        }
    }
}


def mattermost_bold_text(value):
    return f"**{value}**"


def mattermost_mention_text(value):
    return f"@{value}"


mattermost_env = Environment()
mattermost_env.filters['mattermost_bold_text'] = mattermost_bold_text
mattermost_env.filters['mattermost_mention_text'] = mattermost_mention_text
mattermost_users_template_string = "{{ users | map('mattermost_bold_text') | join(', ') }}"
mattermost_admins_template_string = "{{ users | map('mattermost_mention_text') | join(', ') }}"
