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
