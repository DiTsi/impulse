class MainRoute:
    def __init__(self, action, routes_list):
        self.action = action
        self.routes = []
        for r in routes_list:
            if r.get('routes') is None:
                self.routes.append(Route(r.get('action'), [], r.get('matchers')))
            else:
                self.routes.append(Route(r.get('action'), r.get('routes'), r.get('matchers')))

    def __repr__(self):
        return self.action


class Route(MainRoute):
    def __init__(self, action, routes_list, matchers):
        super().__init__(action, routes_list)
        self.matchers = matchers
