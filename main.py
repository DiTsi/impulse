import json
import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import request, Flask

from app.chain import generate_chains
from app.channel import generate_channels
from app.incident import Incident, Incidents
from app.logger import logger
from app.message_template import generate_message_templates
from app.queue import Queue, unix_sleep_to_timedelta
from app.route import generate_route
from app.schedule import Action, Schedule, generate_queue
from app.slack import get_public_channels, create_thread, post_thread, get_users
from app.unit import generate_units
from config import settings
from config import slack_verification_token

app = Flask(__name__)
incidents = Incidents([])
incidents_directory = settings.get('incidents_directory')


def recreate_incidents():
    global incidents
    global incidents_directory

    for path, directories, files in os.walk(incidents_directory):
        for filename in files:
            incidents.add(Incident.load(f'{incidents_directory}/{filename}'))


def handle_queue():
    schedule = queue.handle_first()
    if schedule is not None:
        incident = incidents.by_uuid.get(schedule.action.id)
        if schedule.action.type == 'slack_mention':
            unit = units.get(schedule.action.to)
            text = unit.mention_text()
            post_thread(incident.channel_id, incident.ts, text)
        elif schedule.action.type == 'webhook':
            pass
        elif schedule.action.type == 'change_status':
            incident.update_status(schedule.action.to)


def handle_new(alert_state):
    channel_id, chain_name = route.get_route(alert_state)
    channel = channels[channel_id]
    template = message_templates.get(channel.message_template)
    message = template.form_message(alert_state)
    ts = create_thread(
        channel_id=channel.id,
        message=message,
        status=alert_state['status']
    )
    incident = Incident(
        alert=alert_state,
        status=alert_state['status'],
        ts=ts,
        channel_id=channel.id,
        channel_type=channel.type,
        scheduler=[],
        acknowledged=False,
        acknowledged_by=None,
        updated=datetime.utcnow(),
        message=message
    )

    chain = chains[chain_name]
    uuid = incidents.add(incident)
    status = alert_state.get("status")

    action = Action(uuid, 'change_status', 'unknown')
    schedule_list = [Schedule(
        datetime_=datetime.utcnow() + unix_sleep_to_timedelta(settings.get(f'{status}_timeout')),
        action=action,
        status=status
    )] + generate_queue(uuid, units, chain.steps)

    incident.set_queue(schedule_list)
    queue.put(schedule_list)
    # incident.dump(f'{incidents_directory}/{channel.name}_{ts}.yml')


def handle_existing(incident, alert_state):
    channel = channels[incident.channel_id]
    template = message_templates.get(channel.message_template)
    if incident.last_state != alert_state:
        logger.debug(f'Incident get new state')
        incident.update(alert_state, template.form_message(alert_state))
        # incident.dump(f'{incidents_directory}/{channel.name}_{incident.ts}.yml')
    else:
        logger.debug(f'Incident get same state')


@app.route('/queue', methods=['GET'])
def get_queue():
    return queue.serialize(), 200


@app.route('/', methods=['POST'])
def receive_alert():
    global incidents
    global incidents_directory

    alert_state = request.json

    incident = incidents.get(alert=alert_state)
    if incident is None:
        handle_new(alert_state)
    else:
        handle_existing(incident, alert_state)
    return alert_state, 200


@app.route('/slack', methods=['POST'])
def slack_button():
    payload = json.loads(request.form['payload'])
    if payload.get('token') != slack_verification_token:
        logger.error(f'Unauthorized request to \'/slack\'')
        return {}, 401
    modified_message = payload.get('original_message')
    if modified_message['attachments'][1]['actions'][0]['text'] == 'Acknowledge':
        modified_message['attachments'][1]['actions'][0]['text'] = 'Unacknowledge'
        modified_message['attachments'].append({
            'color': modified_message['attachments'][1].get('color'),
            'text': f"Acknowledged by <@{payload['user']['id']}>"
        })
    else:
        modified_message['attachments'][1]['actions'][0]['text'] = 'Acknowledge'
        del modified_message['attachments'][2]
    return modified_message, 200


if __name__ == '__main__':
    if not os.path.exists(incidents_directory):
        logger.debug(f'Creating incidents_directory')
        os.makedirs(incidents_directory)
        logger.debug(f'Created incidents_directory')

    logger.debug(f'Recreate incidents from disk')
    recreate_incidents()

    # read config
    channels_dict = settings.get('channels')
    units_dict = settings.get('units')
    message_templates_dict = settings.get('message_templates')
    route_dict = settings.get('route')
    chains_dict = settings.get('chains')

    # get existing channels info from Slack
    logger.debug(f'Get Slack channels using API')
    slack_channels = get_public_channels()

    # get existing channels info from Slack
    logger.debug(f'Get Slack users using API')
    slack_users = get_users()

    # create objects from config
    channels = generate_channels(channels_dict, slack_channels)
    units = generate_units(units_dict, slack_users)
    message_templates = generate_message_templates(message_templates_dict)
    route = generate_route(route_dict, slack_channels)
    chains = generate_chains(chains_dict)

    # create Queue object
    logger.debug(f'Creating Queue')
    queue = Queue()
    logger.debug(f'Queue created')

    # run scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=handle_queue, trigger="interval", seconds=1.5)
    scheduler.start()

    # flog.default_handler.setFormatter(CustomFormatter())
    app.run(host='0.0.0.0', port=5000)
