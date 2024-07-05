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
