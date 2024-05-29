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
    def __init__(self, channel, chain, routes_list):
        self.channel = channel
        self.chain = chain or None
        self.routes = []
        for r in routes_list:
            if r.get('routes') is None:
                route = Route(r.get('channel'), r.get('chain'), [], r.get('matchers'))
                self.routes.append(route)
            else:
                route = Route(r.get('channel'), r.get('chain'), r.get('routes'), r.get('matchers'))
                self.routes.append(route)

    def get_route(self, alert_state):
        if len(self.routes) == 0:
            return self.channel, self.chain
        else:
            for r in self.routes:
                match, channel, chain = r.get_route(alert_state)
                if match:
                    return channel, chain
            return self.channel, self.chain

    def get_uniq_channels(self):
        channels = list()
        channels.append(self.channel)
        for r in self.routes:
            if len(r.routes) == 0:
                channels.append(r.channel)
            else:
                channels = r.get_channels(channels)
        return set(channels)

    def __repr__(self):
        return self.chain


class Route(MainRoute):
    def __init__(self, channel, chain, routes_list, matchers):
        super().__init__(channel, chain, routes_list)
        self.matchers = [Matcher(m) for m in matchers]

    def get_route(self, alert_state):
        for m in self.matchers:
            if not m.matches(alert_state):
                return False, None, None
        if len(self.routes) == 0:
            return True, self.channel, self.chain
        else:
            for r in self.routes:
                match, channel, chain = r.get_route(alert_state)
                if match:
                    return True, channel, chain
            return True, self.channel, self.chain

    def get_channels(self, channels):
        channels.append(self.channel)
        if len(self.routes) != 0:
            for r in self.routes:
                channels = r.get_channels(channels)
                pass
        return channels


def generate_route(route_dict):
    logger.debug(f'Creating MainRoute')
    main_channel_name = route_dict['channel']
    main_chain = route_dict.get('chain')
    routes = route_dict.get('routes')

    route = MainRoute(main_channel_name, main_chain, routes)
    logger.debug(f'MainRoute created')
    return route
