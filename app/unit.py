from app.logger import logger


class Unit:
    def __init__(self, name, slack_id=None, webhook=None):
        self.name = name
        self.slack_id = slack_id
        self.webhook = webhook

    def __repr__(self):
        return self.name

    def mention_text(self):
        text = f'notify unit *{self.name}*: <@{self.slack_id}>'
        return text


class UnitGroup:
    def __init__(self, name, units):
        self.name = name
        self.units = units

    def get_actions(self, action):
        if action == 'webhook':
            return [u.webhook for u in self.units]
        elif action == 'mention':
            return [u.slack_mention for u in self.units]

    def mention_text(self):
        text = f'notify unit_group *{self.name}*. Units:'
        for unit in self.units:
            text += f'\n<@{unit.slack_id}> '
        return text


def generate_units(units_dict, slack_users):
    def get_user_id_(s_users, user):
        if user is None:
            return None
        for u in s_users:
            if u.get('real_name') == user:
                return u['id']
        logger.warning(f'User \'{user}\' not found in Slack users')
        return None

    logger.debug(f'Creating Units')
    units = {}
    for name in units_dict.keys():
        slack_name = units_dict[name]['notify_types'].get('slack_mention')
        slack_id = get_user_id_(slack_users, slack_name)
        webhook = units_dict[name]['notify_types'].get('webhook')
        units[name] = Unit(name, slack_id=slack_id, webhook=webhook)
    return units


def generate_unit_groups(unit_groups_dict, units):
    logger.debug(f'Creating UnitGroups')
    unit_groups = {}
    for name in unit_groups_dict.keys():
        unit_names = unit_groups_dict[name]['units']
        unit_objects = [units.get(unit_name) for unit_name in unit_names]
        unit_groups[name] = UnitGroup(name, unit_objects)
    logger.debug(f'UnitGroups created')
    return unit_groups
