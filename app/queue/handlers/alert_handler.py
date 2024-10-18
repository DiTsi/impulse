from datetime import datetime

from app.im.template import JinjaTemplate, update_alerts
from app.incident.incident import IncidentConfig, Incident
from app.logging import logger
from app.queue.handlers.base_handler import BaseHandler
from app.time import unix_sleep_to_timedelta
from config import timeouts, INCIDENT_ACTUAL_VERSION, incident, experimental


class AlertHandler(BaseHandler):
    """
    AlertHandler class is responsible for handling the alert event.

    :param queue: Queue instance
    :param application: Application instance
    :param incidents: Incidents instance
    :param route: Route instance
    """
    __slots__ = ['queue', 'application', 'incidents', 'route']

    def __init__(self, queue, application, incidents, route):
        super().__init__(queue, application, incidents)
        self.route = route

    def handle(self, alert_state):
        incident_ = self.incidents.get(alert=alert_state)
        if incident_ is None:
            self._handle_create(alert_state)
        else:
            logger.debug(f'New Alertmanager event for incident {incident_.uuid}:')
            logger.debug(f'{alert_state}')
            self._handle_update(incident_.uuid, incident_, alert_state)

    def _handle_create(self, alert_state):
        channel_name, chain_name = self.route.get_route(alert_state)
        channel = self.app.channels[channel_name]

        status = alert_state['status']
        updated_datetime = datetime.utcnow()
        status_update_datetime = datetime.utcnow() + unix_sleep_to_timedelta(timeouts.get(status))

        chain = self.app.chains.get(chain_name)
        config = IncidentConfig(
            application_type=self.app.type,
            application_url=self.app.url,
            application_team=self.app.team
        )
        incident_ = Incident(
            last_state=alert_state,
            status=status,
            channel_id=channel['id'],
            config=config,
            chain=[],
            chain_enabled=True,
            status_enabled=True,
            updated=updated_datetime,
            status_update_datetime=status_update_datetime,
            version=INCIDENT_ACTUAL_VERSION
        )
        self._create_thread(incident_, alert_state)
        self.incidents.add(incident_)

        logger.info(f'Incident {incident_.uuid} created. Link: {incident_.link}')
        [logger.info(f'  {i}: {alert_state["groupLabels"][i]}') for i in alert_state['groupLabels'].keys()]
        logger.debug(f'{alert_state}')

        self.queue.put(status_update_datetime, 'update_status', incident_.uuid)

        incident_.generate_chain(chain)
        self.queue.recreate(incident_.uuid, incident_.chain)
        incident_.dump()

    def _recreate_chain_in_queue(self, uuid_, incident_):
        chain = incident_.get_chain()
        self.queue.recreate(uuid_, chain)

    def _handle_update(self, uuid_, incident_, alert_state):
        prev_status = incident_.status
        if alert_state.get('status') == 'firing':
            self._recreate_chain_in_queue(uuid_, incident_)
        is_status_updated, is_state_updated, new_alerts_fir, old_alerts_res = incident_.update_state(alert_state)
        if is_state_updated or is_status_updated:
            if experimental.get('release_incident_and_recreate_chain_by_new_firing_alerts') and new_alerts_fir:
                incident_.chain_enabled = True
            self.app.update(
                uuid_, incident_, alert_state['status'], alert_state, is_status_updated,
                incident_.chain_enabled, incident_.status_enabled
            )
        if prev_status == 'firing':
            self._handle_new_alerts(uuid_, alert_state, incident_, new_alerts_fir, old_alerts_res)
        self.queue.update(uuid_, incident_.status_update_datetime, incident_.status)

    def _handle_new_alerts(self, uuid_, alert_state, incident_, new_alerts_fir, old_alerts_res):
        if not new_alerts_fir and not old_alerts_res:
            return

        recreate_chain = experimental.get('release_incident_and_recreate_chain_by_new_firing_alerts')
        if recreate_chain and new_alerts_fir:
            self.queue.delete_by_id(incident_.uuid, delete_steps=True, delete_status=False)

            _, chain_name = self.route.get_route(alert_state)
            chain = self.app.chains.get(chain_name)
            incident_.generate_chain(chain)
            self.queue.recreate(incident_.uuid, incident_.chain)
            incident_.dump()

            logger.info(f"Incident {uuid_} chain recreated")
        if recreate_chain or incident.get('new_firing_alerts_notifications'):
            header = self.app.format_text_italic(
                self.app.header_template.form_message(incident_.last_state, incident_)
            )
            fields = {'type': self.app.type, 'firing': new_alerts_fir, 'recreate': recreate_chain}
            text_template = JinjaTemplate(update_alerts)
            text = text_template.form_notification(fields)

            message = header + '\n' + text
            self.app.post_thread(incident_.channel_id, incident_.ts, message)
            if new_alerts_fir:
                logger.info(f"Incident {uuid_} updated with new alerts firing")
            else:
                logger.info(f"Incident {uuid_} updated with some alerts resolved")

    def _create_thread(self, incident_, alert_state):
        body = self.app.body_template.form_message(alert_state, incident_)
        header = self.app.header_template.form_message(alert_state, incident_)
        status_icons = self.app.status_icons_template.form_message(alert_state, incident_)
        thread_id = self.app.create_thread(
            incident_.channel_id, body, header, status_icons, status=alert_state['status']
        )
        incident_.set_thread(thread_id)
        return thread_id
