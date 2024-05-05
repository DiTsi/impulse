import re

from app.logger import logger


class Matcher:
    re_type = re.compile('(?P<label>\w+)\s?(?P<type>=|!=|=~|!~)\s?"(?P<expr>.+)"')

    def __init__(self, string):
        m = Matcher.re_type.match(string)
        if not m:
            logger.debug(f'Cannot use matcher \"{string}\"')
        self.type = m.group('type')
        self.label = m.group('label')
        self.expr = m.group('expr')
        if self.type in ['=~', '!~']:
            self.regex = re.compile(self.expr)

    def matches(self, alert_state):
        if self.type == '=':
            if alert_state.get('commonLabels').get(self.label) == self.expr:
                return True
            else:
                return False
        elif self.type == '!=':
            if alert_state.get('commonLabels').get(self.label) == self.expr:
                return False
            else:
                return True
        elif self.type == '=~':
            expr = alert_state.get('commonLabels').get(self.label)
            if self.regex.match(expr):
                return True
            else:
                return False
        else:
            expr = alert_state.get('commonLabels').get(self.label)
            if self.regex.match(expr):
                return False
            else:
                return True


class MainRoute:
    def __init__(self, channel_id, chain, routes_list):
        self.channel_id = channel_id
        self.chain = chain or None
        self.routes = []
        for r in routes_list:
            if r.get('routes') is None:
                self.routes.append(Route(r.get('channel_id'), r.get('chain'), [], r.get('matchers')))
            else:
                self.routes.append(Route(r.get('channel_id'), r.get('chain'), r.get('routes'), r.get('matchers')))

    def get_route(self, alert_state):
        if len(self.routes) == 0:
            return self.channel_id, self.chain
        else:
            for r in self.routes:
                match, channel_id, chain = r.get_route(alert_state)
                if match:
                    return channel_id, chain
            return self.channel_id, self.chain

    def __repr__(self):
        return self.chain


class Route(MainRoute):
    def __init__(self, channel_id, chain, routes_list, matchers):
        super().__init__(channel_id, chain, routes_list)
        self.matchers = [Matcher(m) for m in matchers]

    def get_route(self, alert_state):
        for m in self.matchers:
            if not m.matches(alert_state):
                return False, None, None
        if len(self.routes) == 0:
            return True, self.channel_id, self.chain
        else:
            for r in self.routes:
                match, channel_id, chain = r.get_route(alert_state)
                if match:
                    return True, channel_id, chain
            return True, self.channel_id, self.chain


def generate_route(route_dict, slack_channels):
    def add_channel_ids(routes, slack_channels):
        for r in routes:
            ch = r['channel']
            try:
                r['channel_id'] = slack_channels[ch]['id']
                if 'routes' in r:
                    rs = r['routes']
                    add_channel_ids(rs, slack_channels)
            except KeyError:
                logger.error(f'No channel \'{ch}\' in Slack')


    logger.debug(f'Creating MainRoute')
    main_channel_name = route_dict['channel']
    main_channel_id = slack_channels[main_channel_name]['id']
    main_chain = route_dict.get('chain')
    routes = route_dict.get('routes')

    # replace channel name with channel_id
    add_channel_ids(routes, slack_channels)

    route = MainRoute(main_channel_id, main_chain, routes)
    logger.debug(f'MainRoute created')
    return route
