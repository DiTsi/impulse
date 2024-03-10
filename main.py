from flask import request, jsonify, Flask

from app.message_template import MessageTemplate
from app.thread import Thread
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

    message_templates_list = settings.get('message_templates')
    threads_list = settings.get('threads')
    channels_list = settings.get('channels')

    threads_dict = {t.get('name'): t.get('steps') for t in threads_list}
    message_templates_dict = {t.get('name'): t.get('text') for t in message_templates_list}

    channels = {c.get('name'): Channel(
        c.get('id'),
        c.get('name'),
        MessageTemplate(c.get('message_template'), message_templates_dict.get(c.get('message_template'))),
        [Thread(t, threads_dict[t]) for t in c.get('threads')],
    ) for c in channels_list}

    incidents = []
    app.run(host='0.0.0.0', port=5000)
