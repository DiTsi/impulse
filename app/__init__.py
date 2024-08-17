from app.im.mattermost.buttons import mattermost_buttons_handler
from app.im.slack.buttons import slack_buttons_handler


def buttons_handler(app, payload, incidents, queue):
    if app.type == 'slack':
        return slack_buttons_handler(payload, incidents, queue)
    else:
        return mattermost_buttons_handler(app, payload, incidents, queue)
