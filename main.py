import json

from apscheduler.schedulers.background import BackgroundScheduler
from flask import request, Flask, redirect, url_for

from app import (alert_handle, queue_handle, recreate_queue, Incidents, create_or_load_incidents, generate_webhooks,
                 generate_route, buttons_handler)
from app.im import Application
from config import settings, check_updates

app = Flask(__name__)
incidents = Incidents([])


@app.route('/queue', methods=['GET'])
def get_queue():
    return queue.serialize(), 200


@app.route('/', methods=['POST', 'GET'])
def receive_alert():
    if request.method == 'POST':
        alert_state = request.json
        alert_handle(application, route, incidents, queue, alert_state)
        return alert_state, 200
    else:
        return redirect(url_for('get_incidents'))


@app.route('/app', methods=['POST', 'PUT'])
def buttons_handler():
    if application.type == 'slack':
        payload = json.loads(request.form['payload'])
    else:
        payload = request.json
    return buttons_handler(application, payload, incidents, queue)


@app.route('/incidents', methods=['GET'])
def get_incidents():
    return incidents.serialize(), 200


if __name__ == '__main__':
    latest_tag = {'version': None}

    route_dict = settings.get('route')
    app_dict = settings.get('application')
    webhooks_dict = settings.get('webhooks')

    route = generate_route(route_dict)
    application = Application(
        app_dict,
        route.get_uniq_channels(),
        route.channel
    )
    webhooks = generate_webhooks(webhooks_dict)

    incidents = create_or_load_incidents(application.type, application.url, application.team)
    queue = recreate_queue(incidents, check_updates)

    # run scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=queue_handle,
        trigger="interval",
        seconds=1.1,
        args=[incidents, queue, application, webhooks, latest_tag]
    )
    scheduler.start()

    app.run(host='0.0.0.0', port=5000)
