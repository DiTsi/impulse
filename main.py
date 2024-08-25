import json

from apscheduler.schedulers.background import BackgroundScheduler
from flask import request, Flask, redirect, url_for

from app import buttons_handler
from app.alerts import alert_handle
from app.im.helpers import get_application
from app.incident.incidents import Incidents
from app.queue import recreate_queue, queue_handle
from app.route import generate_route
from app.webhook import generate_webhooks
from config import settings, check_updates


app = Flask(__name__)
latest_tag = {'version': None}

route_dict = settings.get('route')
app_dict = settings.get('application')
webhooks_dict = settings.get('webhooks')

route = generate_route(route_dict)
application = get_application(
    app_dict,
    route.get_uniq_channels(),
    route.channel
)
webhooks = generate_webhooks(webhooks_dict)
incidents = Incidents.create_or_load(application.type, application.url, application.team)
queue = recreate_queue(incidents, check_updates)
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=queue_handle,
    trigger="interval",
    seconds=1.1,
    args=[incidents, queue, application, webhooks, latest_tag]
)
scheduler.start()


def create_app():
    return app


@app.route('/queue', methods=['GET'])
def route_queue_get():
    return queue.serialize(), 200


@app.route('/', methods=['POST', 'GET'])
def route_alert_post():
    if request.method == 'POST':
        alert_state = request.json
        alert_handle(application, route, incidents, queue, alert_state)
        return alert_state, 200
    else:
        return redirect(url_for('route_incidents_get'))


@app.route('/app', methods=['POST', 'PUT'])
def route_app_buttons():
    if application.type == 'slack':
        payload = json.loads(request.form['payload'])
    else:
        payload = request.json
    return buttons_handler(application, payload, incidents, queue)


@app.route('/incidents', methods=['GET'])
def route_incidents_get():
    return incidents.serialize(), 200


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
