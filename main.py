from flask import request, jsonify, Flask

from app.mention import Mention
from app.message_template import MessageTemplate
from app.thread import Thread
from app.route import MainRoute
from slack.channels import SlackChannel as Channel
from config import settings


app = Flask(__name__)


@app.route('/', methods=['POST'])
def receive_alert():
    data = request.json
    print(data)
    return jsonify({'message': 'Alert received successfully'}), 200


# @app.route('/', methods=['POST'])
# def receive_alert():
#     data = request.json
#     print("Received alert:")
#     print(data)
#     return jsonify({'message': 'Alert received successfully'}), 200


if __name__ == '__main__':

    channels_list = settings.get('channels')
    mentions = settings.get('mentions')
    message_templates_list = settings.get('message_templates')
    route_dict = settings.get('route')
    threads_list = settings.get('threads')

    channels = {c.get('name'): Channel(
        c.get('id'),
        c.get('name'),
        c.get('message_template'),
        c.get('threads'),
    ) for c in channels_list}
    mentions = {
        m.get('name'): Mention(m.get('name'), m.get('units')) for m in mentions
    }
    message_templates = {
        mt.get('name'): MessageTemplate(mt.get('name'), mt.get('text')) for mt in message_templates_list
    }
    route = MainRoute(route_dict.get('thread'), route_dict.get('routes'))
    threads = {
        t.get('name'): Thread(t.get('name'), t.get('steps')) for t in threads_list
    }

    # Verify all objects exists
    # verify all route threads exists in channel threads and only in one
    #


    incidents = []
    app.run(host='0.0.0.0', port=5000)
