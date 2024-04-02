import json
import os

from flask import request, jsonify, Flask

from app.chain import Chain
from app.channel import SlackChannel as Channel
from app.incident import Incident, Incidents, load_incident
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
            incident = load_incident(f'{incidents_directory}/{filename}')
            incidents.add(incident)


@app.route('/', methods=['POST'])
def receive_alert():
    global incidents
    global incidents_directory

    data = request.json #!
    e = incidents
    incident = incidents.get(alert=data)
    if incident is not None:
        incident.update(data)
    else:
        matched_chain = route.get_chain(data)
        chain = chains.get(matched_chain)
        channel_name = chain_channel.get(chain.name)
        template = message_templates.get(channels.get(channel_name).message_template)
        incident = Incident(
            alert=data,
            channel=channel_name,
            steps=None,
            chain=chain,
            template=template,
            ts=None
        )
        incidents.add(incident)
        incident.dump(incidents_directory)
        e = incidents
    return data, 200


@app.route('/slack', methods=['POST'])
def slack_button():
    payload = json.loads(request.form['payload'])
    if payload.get('token') != slack_verification_token:
        print(f'Unauthorized!') #!
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

    channels_list = settings.get('channels')
    units_list = settings.get('units')
    message_templates_list = settings.get('message_templates')
    route_dict = settings.get('route')
    chains_list = settings.get('chains')

    channels = {c.get('name'): Channel(
        c.get('id'),
        c.get('name'),
        c.get('message_template'),
        c.get('chains'),
    ) for c in channels_list}
    units = {}
    for u in units_list:
        if 'actions' in u:
            units[u.get('name')] = Unit(u.get('name'), u.get('actions'))
    for u in units_list:
        if 'units' in u:
            units[u.get('name')] = UnitGroup(u.get('name'), [units[unitname] for unitname in u.get('units')])
    message_templates = {
        mt.get('name'): MessageTemplate(mt.get('name'), mt.get('text')) for mt in message_templates_list
    }
    route = MainRoute(route_dict.get('action'), route_dict.get('routes'))
    chains = {
        t.get('name'): Chain(t.get('name'), t.get('steps')) for t in chains_list
    }

    chain_channel = {}
    for c_name, c_object in channels.items():
        for a in c_object.chains:
            chain_channel[a] = c_name

    # TEST ALERT
    # with open('response.json', 'r') as file:
    #     json_string = file.read()
    # json_string = json_string.replace('"', '\\"')
    # json_string = json_string.replace("'", '"')
    # alert = json.loads(json_string)
    # with app.app_context():
    #     r = receive_alert(alert)

    app.run(host='0.0.0.0', port=5000)
