import re


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
