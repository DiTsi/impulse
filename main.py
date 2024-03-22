import json

from flask import request, jsonify, Flask

from app.chain import Chain
from app.channel import SlackChannel as Channel
from app.incident import Incident
from app.unit import Unit, UnitGroup
from app.message_template import MessageTemplate
from app.route import MainRoute
from config import settings
from config import slack_verification_token

app = Flask(__name__)
incident_channels = dict()


@app.route('/', methods=['POST'])
def receive_alert():
    data = request.json
    print(data)
    return jsonify({'message': 'Alert received successfully'}), 200


@app.route('/slack', methods=['POST'])
def slack_button():
    r = json.loads(request.form['payload'])
    if r.get('token') != slack_verification_token:
        print(f'Unauthorized!') #!
        return {}, 401
    channel = r.get('channel')
    ch_name = channel.get('name')
    user = r.get('user')
    message_ts = r.get('message_ts')
    inc = incident_channels.get(ch_name).get(message_ts)
    inc.acknowledge(user.get('id'))
    return {}, 200


if __name__ == '__main__':

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

    with open('response.json', 'r') as file:
        json_string = file.read()
    json_string = json_string.replace('"', '\\"')
    json_string = json_string.replace("'", '"')
    alert = json.loads(json_string)
    matched_chain = route.get_chain(alert)
    if matched_chain == 'IGNORE':
        pass
    chain = chains.get(matched_chain)
    channel_name = chain_channel.get(chain.name)
    template = message_templates.get(channels.get(channel_name).message_template)

    # Incident(alert, )
    if channel_name not in incident_channels.keys():
        incident_channels[channel_name] = {}
    i = Incident(alert, channel_name, template)
    incident_channels[channel_name][i.ts] = i

    app.run(host='0.0.0.0', port=5000)
