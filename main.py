import json

from apscheduler.schedulers.background import BackgroundScheduler
from flask import request, Flask

from app import queue_handle, handle_alert, slack_handler
from app.incident import Incidents, recreate_incidents
from app.logger import logger
from app.queue import Queue
from app.route import generate_route
from app.slack.application import generate_application
from config import settings

app = Flask(__name__)
incidents = Incidents([])


@app.route('/queue', methods=['GET'])
def get_queue():
    return queue.serialize(), 200


@app.route('/', methods=['POST'])
def receive_alert():
    alert_state = request.json
    handle_alert(application, route, incidents, queue, alert_state)
    return alert_state, 200


@app.route('/slack', methods=['POST'])
def handler():
    payload = json.loads(request.form['payload'])
    return slack_handler(payload, incidents, queue)


@app.route('/incidents', methods=['GET'])
def get_incidents():
    return incidents.serialize(), 200


if __name__ == '__main__':
    incidents = recreate_incidents()

    route_dict = settings.get('route')
    app_dict = settings.get('application')
    webhooks_dict = settings.get('webhooks')

    route = generate_route(route_dict)
    application = generate_application(
        app_dict,
        channels_list=route.get_uniq_channels()
    )

    # create Queue object
    logger.debug(f'Creating Queue')
    queue = Queue()
    logger.debug(f'Queue created')

    # run scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=queue_handle,
        trigger="interval",
        seconds=1.5,
        args=[incidents, queue, application, webhooks_dict]
    )
    scheduler.start()

    # flog.default_handler.setFormatter(CustomFormatter())
    app.run(host='0.0.0.0', port=5000)
