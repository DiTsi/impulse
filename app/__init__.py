from .alerts import alert_handle, alert_handle_create, alert_handle_update
from .im import slack_buttons_handler, mattermost_buttons_handler
from .incident import Incident, Incidents, recreate_incidents
from app.logging import logger
from .queue import unix_sleep_to_timedelta, Queue, queue_handle, recreate_queue
from .route import generate_route
from .update import get_latest_tag
from .webhook import generate_webhooks


def handler(app, payload, incidents, queue):
    if app.type == 'slack':
        return slack_buttons_handler(payload, incidents, queue)
    else:
        return mattermost_buttons_handler(app, payload, incidents, queue)
