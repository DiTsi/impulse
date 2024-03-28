import json
import uuid
from datetime import datetime

import yaml

from app.channel import SlackChannels
from app.slack import update_thread, create_thread
from app.slack import get_public_channels


public_channels_dict = get_public_channels()
public_channels = SlackChannels(public_channels_dict)


class Incident:
    def __init__(self, alert, channel, template, chain):
        self.last_state = alert
        self.channel = channel
        self.steps = chain.serialize()
        self.updated = datetime.utcnow()
        self.ts = create_thread(
            channel_id=public_channels.get_by_name(channel).id,
            message=template.form_message(alert),
            status=alert.get('status'),
        )
        pass

    def dump(self, incidents_directory):
        with open(f'{incidents_directory}/{self.channel}_{self.ts}.yml', 'w') as f:
            yaml.dump(self, f, default_flow_style=False)

    def update(self, alert, template):
        self.last_state = alert
        self.updated = datetime.utcnow()
        update_thread(
            channel_id=public_channels.get_by_name(self.channel).id,
            ts=self.ts,
            status=alert.get('status'),
            message=template.form_message(alert),
        )

    def acknowledge(self, user_id, template):
        update_thread(
            channel_id=public_channels.get_by_name(self.channel).id,
            ts=self.ts,
            status=self.last_state.get('status'),
            message=template.form_message(self.last_state),
            acknowledge=True,
            user_id=user_id,
        )

        pass


class Incidents:
    def __init__(self, incidents_list):
        self.by_uuid = {gen_uuid(i.last_state.get('groupLabels')): i for i in incidents_list}
        self.by_ts = {gen_uuid(i.channel + i.ts): i for i in incidents_list}

    def get(self, alert=None, channel=None, ts=None):
        if alert is not None:
            uuid = gen_uuid(alert.get('groupLabels'))
            return self.by_ts.get(uuid)
        else:
            ts_id = gen_uuid(channel + ts)
            return self.by_ts.get(ts_id)

    def add(self, incident):
        self.by_uuid[gen_uuid(incident.last_state.get('groupLabels'))] = incident
        self.by_ts[gen_uuid(incident.channel + incident.ts)] = incident

    def delete(self, alert, channel, ts):
        if alert is not None:
            uuid = gen_uuid(alert.get('groupLabels'))
            del self.by_uuid[uuid]
            # удалится по ts?
            pass
        else:
            ts_id = gen_uuid(channel + ts)
            del self.by_ts[ts_id]
            # удалится по uuid?
            pass

    # def serialize(self):
    #     return {
    #         'chain': self.chain,
    #         'channel_id': self.channel_id,
    #         'channel_name': self.channel_name,
    #         'created': self.created,
    #         'group_labels': self.group_labels,
    #         'last_state': self.last_state,
    #         'status': self.status,
    #         'steps': self.steps,
    #         'template': self.template,
    #         'updated': self.updated,
    #     }

# def create_slack_thread(channel_name, message, color, acknowledge):
#     url = 'https://slack.com/api/chat.postMessage'
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {slack_bot_user_oauth_token}',
#     }
#     try:
#         response = requests.post(url, headers=headers, data=json.dumps(payload))
#         if response.status_code != 200:
#             print(f"Failed to send message to Slack. Status code: {response.status_code}")
#         json_ = response.json()
#         return json_.get('channel'), json_.get('ts')
#     except requests.exceptions.RequestException as e:
#         print(f'Failed to send message: {e}')  # !


def gen_uuid(data):
    return uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(data))
