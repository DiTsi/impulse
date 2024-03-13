import re


class Matcher:
    re_type = re.compile('(?P<label>\w+)\s?(?P<type>=|!=|=~|!~)\s?"(?P<expr>.+)"')

    def __init__(self, string):
        m = Matcher.re_type.match(string)
        if not m:
            print(f'Cannot use matcher \"{string}\"')
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
    def __init__(self, action, routes_list):
        self.action = action
        self.routes = []
        for r in routes_list:
            if r.get('routes') is None:
                self.routes.append(Route(r.get('action'), [], r.get('matchers')))
            else:
                self.routes.append(Route(r.get('action'), r.get('routes'), r.get('matchers')))

    def get_action(self, alert_state):
        if len(self.routes) == 0:
            return self.action
        else:
            for r in self.routes:
                match, action = r.get_action(alert_state)
                if match:
                    return action
            return self.action

    def __repr__(self):
        return self.action


class Route(MainRoute):
    def __init__(self, action, routes_list, matchers):
        super().__init__(action, routes_list)
        self.matchers = [Matcher(m) for m in matchers]

    def get_action(self, alert_state):
        for m in self.matchers:
            if not m.matches(alert_state):
                return False, None
        if len(self.routes) == 0:
            return True, self.action
        else:
            for r in self.routes:
                match, action = r.get_action(alert_state)
                if match:
                    return True, action
            return True, self.action
