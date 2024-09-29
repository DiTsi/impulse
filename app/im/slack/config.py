from jinja2 import Environment

from config import slack_bot_user_oauth_token

slack_headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {slack_bot_user_oauth_token}',
}
buttons = {
    # styles: normal, danger
    'chain': {
        'enabled': {
            'text': '◼ Chain',
            'style': 'primary'
        },
        'disabled': {
            'text': '▶ Chain',
            'style': 'normal'
        }
    },
    'status': {
        'enabled': {
            'text': '◼ Status',
            'style': 'primary'
        },
        'disabled': {
            'text': '▶ Status',
            'style': 'normal'
        }
    }
}
slack_request_delay = 1.5  # seconds


def slack_normal_text(value):
    return f"{value}"


def slack_bold_text(value):
    return f"*{value}*"


def slack_mention_text(value):
    return f"<@{value}>"


slack_env = Environment()
slack_env.filters['slack_bold_text'] = slack_bold_text
slack_env.filters['slack_mention_text'] = slack_mention_text
slack_admins_template_string = "{{ users | map('slack_mention_text') | join(', ') }}"
