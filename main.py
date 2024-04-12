from datetime import datetime
import json
import os

from flask import request, Flask

from app.chain import Chain, generate_queue, Schedule
from app.channel import SlackChannels
from app.incident import Incident, Incidents
from app.logger import logger
from app.slack import get_public_channels, create_thread
from app.unit import Unit, UnitGroup
from app.message_template import MessageTemplate
from app.route import MainRoute
from config import settings
from config import slack_verification_token


app = Flask(__name__)
incidents = Incidents([])
incidents_directory = settings.get('incidents_directory')


def prepare():
    incidents_dir = settings.get('incidents_directory')
    if not os.path.exists(incidents_dir):
        os.makedirs(incidents_dir)

    # check all the Incidents have actual channels and chains
    # recreate if it was changed by rules
    recreate_incidents()


def recreate_incidents():
    global incidents
    global incidents_directory

    for path, directories, files in os.walk(incidents_directory):
        for filename in files:
            incidents.add(Incident.load(f'{incidents_directory}/{filename}'))


@app.route('/', methods=['POST'])
def receive_alert():
    global incidents
    global incidents_directory

    alert_state = request.json

    incident = incidents.get(alert=alert_state)
    if incident is None:
        chain_name = route.get_chain(alert_state)
        channel = public_channels.get_by_chain(chain_name)
        template = message_templates.get(channel.message_template)
        ts = create_thread(
            channel_id=channel.id,
            message=template.form_message(alert_state),
            status=alert_state.get('status')
        )
        incident = Incident(
            alert=alert_state,
            ts=ts,
            channel_id=channel.id,
            queue=[],
            acknowledged=False,
            acknowledged_by=None,
            updated=datetime.utcnow(),
        )

        chain = chains[chain_name]
        incident_uuid = incidents.add(incident)
        queue = generate_queue(incident_uuid, units, chain.steps)
        incident.add_queue(queue)

        incident.dump(f'{incidents_directory}/{channel.name}_{ts}.yml')
    else:
        channel = public_channels.channels_by_id[incident.channel_id]
        template = message_templates.get(channel.message_template)
        if incident.last_state != alert_state:
            logger.debug(f'Incident get new state')
            incident.update(alert_state, template.form_message(alert_state))
            incident.dump(f'{incidents_directory}/{channel.name}_{incident.ts}.yml')
        else:
            logger.debug(f'Incident get same state')
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
    prepare()

    channels_dict = settings.get('channels')
    units_dict = settings.get('units')
    message_templates_dict = settings.get('message_templates')
    route_dict = settings.get('route')
    chains_dict = settings.get('chains')

    public_channels = get_public_channels()
    public_channels = SlackChannels(public_channels, channels_dict)

    units = {}
    for name in units_dict.keys():
        if 'actions' in units_dict[name]:
            units[name] = Unit(name, units_dict[name]['actions'])
    for name in units_dict.keys():
        if 'units' in units_dict[name]:
            units[name] = UnitGroup(name, [units[subunit] for subunit in units_dict[name]['units']])
    message_templates = {
        name: MessageTemplate(
            name,
            message_templates_dict[name]['text']
        ) for name in message_templates_dict.keys()
    }
    route = MainRoute(route_dict.get('action'), route_dict.get('routes'))
    chains = {
        name: Chain(name, chains_dict[name]['steps']) for name in chains_dict.keys()
    }

    # TEST ALERT
    # with open('response.json', 'r') as file:
    #     json_string = file.read()
    # json_string = json_string.replace('"', '\\"')
    # json_string = json_string.replace("'", '"')
    # alert = json.loads(json_string)
    # with app.app_context():
    #     r = receive_alert(alert)

    # flog.default_handler.setFormatter(CustomFormatter())
    app.run(host='0.0.0.0', port=5000)
