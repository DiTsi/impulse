from app.alerts import alert_handle, alert_handle_create, alert_handle_update
from app.im.mattermost.buttons import mattermost_buttons_handler
from app.im.slack.buttons import slack_buttons_handler
from app.incident import Incident, Incidents, create_or_load_incidents
from app.logging import logger
from app.queue import Queue, queue_handle, recreate_queue
from app.route import generate_route
from app.update import get_latest_tag
from app.webhook import generate_webhooks


def buttons_handler(app, payload, incidents, queue):
    if app.type == 'slack':
        return slack_buttons_handler(payload, incidents, queue)
    else:
        return mattermost_buttons_handler(app, payload, incidents, queue)
