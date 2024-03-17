import json

from flask import request, jsonify, Flask

from app.action import Action
from app.channel import SlackChannel as Channel
from app.incident import Incident
from app.mention import Mention
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
    mentions = settings.get('mentions')
    message_templates_list = settings.get('message_templates')
    route_dict = settings.get('route')
    actions_list = settings.get('actions')

    channels = {c.get('name'): Channel(
        c.get('id'),
        c.get('name'),
        c.get('message_template'),
        c.get('actions'),
    ) for c in channels_list}
    mentions = {
        m.get('name'): Mention(m.get('name'), m.get('units')) for m in mentions
    }
    message_templates = {
        mt.get('name'): MessageTemplate(mt.get('name'), mt.get('text')) for mt in message_templates_list
    }
    route = MainRoute(route_dict.get('action'), route_dict.get('routes'))
    actions = {
        t.get('name'): Action(t.get('name'), t.get('steps')) for t in actions_list
    }

    # Verify all objects exists
    # verify all route actions exists in channel actions and only in one

    action_channel = {}
    for c_name, c_object in channels.items():
        for a in c_object.actions:
            action_channel[a] = c_name

    with open('response.json', 'r') as file:
        json_string = file.read()
    json_string = json_string.replace('"', '\\"')
    json_string = json_string.replace("'", '"')
    alert = json.loads(json_string)
    matched_action = route.get_action(alert)
    if matched_action == 'IGNORE':
        pass
    action = actions.get(matched_action)
    channel_name = action_channel.get(action.name)
    template = message_templates.get(channels.get(channel_name).message_template)

    # Incident(alert, )
    if channel_name not in incident_channels.keys():
        incident_channels[channel_name] = {}
    i = Incident(alert, channel_name, template)
    incident_channels[channel_name][i.ts] = i

    app.run(host='0.0.0.0', port=5000)
