class MainRoute:
    def __init__(self, thread, routes_list):
        self.thread = thread
        self.routes = []
        for r in routes_list:
            if r.get('routes') is None:
                self.routes.append(Route(r.get('thread'), [], r.get('matchers')))
            else:
                self.routes.append(Route(r.get('thread'), r.get('routes'), r.get('matchers')))

    def __repr__(self):
        return self.thread


class Route(MainRoute):
    def __init__(self, thread, routes_list, matchers):
        super().__init__(thread, routes_list)
        self.matchers = matchers
