import json

from apscheduler.schedulers.background import BackgroundScheduler
from flask import request, Flask, redirect, url_for

from app import (alert_handle, queue_handle, recreate_queue, Incidents, recreate_incidents, generate_webhooks,
                 generate_route, generate_application, handler)
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


@app.route('/slack', methods=['POST'])
def slack_handler():
    payload = json.loads(request.form['payload'])
    return handler(payload, incidents, queue)


@app.route('/incidents', methods=['GET'])
def get_incidents():
    return incidents.serialize(), 200


if __name__ == '__main__':
    latest_tag = {'version': None}
    incidents = recreate_incidents()
    queue = recreate_queue(incidents, check_updates)

    route_dict = settings.get('route')
    app_dict = settings.get('application')
    webhooks_dict = settings.get('webhooks')

    route = generate_route(route_dict)
    application = generate_application(
        app_dict,
        route.get_uniq_channels(),
        route.channel
    )
    webhooks = generate_webhooks(webhooks_dict)

    # run scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=queue_handle,
        trigger="interval",
        seconds=1.1,
        args=[incidents, queue, application, webhooks, latest_tag]
    )
    scheduler.start()

    # flog.default_handler.setFormatter(CustomFormatter())
    app.run(host='0.0.0.0', port=5000)
