from app.logger import logger


class Unit:
    def __init__(self, name, slack_id=None, webhook=None):
        self.name = name
        self.slack_id = slack_id
        self.webhook = webhook

    def __repr__(self):
        return self.name

    def mention_text(self):
        text = f'Notify unit *{self.name}*: <@{self.slack_id}>'
        return text


class UnitGroup(Unit):
    def __init__(self, name, units):
        super().__init__(name, None)
        self.units = units

    def get_actions(self, action):
        if action == 'webhook':
            return [u.webhook for u in self.units]
        elif action == 'mention':
            return [u.slack_mention for u in self.units]

    def mention_text(self):
        text = f'Notify UnitGroup *{self.name}*. Units:'
        for unit in self.units:
            text += f'\n<@{unit.slack_id}> '
        return text


def generate_units(units_dict, slack_users):
    def get_user_id_(users, user):
        if user is None:
            return None
        for u in users:
            if u.get('real_name') == user:
                return u['id']
        logger.warning(f'User \'{user}\' not found in Slack users')
        return None
    logger.debug(f'Creating Units')
    units = {}
    for name in units_dict.keys():
        if 'units' not in units_dict[name]:
            slack_name = units_dict[name]['notify_types'].get('slack_mention')
            slack_id = get_user_id_(slack_users, slack_name)
            webhook = units_dict[name]['notify_types'].get('webhook')
            units[name] = Unit(name, slack_id=slack_id, webhook=webhook)

    logger.debug(f'Creating UnitGroups')
    for name in units_dict.keys():
        if 'units' in units_dict[name]:
            units[name] = UnitGroup(name, [units[subunit] for subunit in units_dict[name]['units']])
    logger.debug(f'Units created')
    return units
