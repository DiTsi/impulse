from config import settings


class MainRoute:
    def __init__(self, receiver, routes_list):
        self.receiver = receiver
        self.routes = []
        for r in routes_list:
            if r.get('routes') is None:
                self.routes.append(Route(r.get('receiver'), [], r.get('matchers'), r.get('continue')))
            else:
                self.routes.append(Route(r.get('receiver'), r.get('routes'), r.get('matchers'), r.get('continue')))


class Route(MainRoute):
    def __init__(self, receiver, routes_list, matchers, continue_):
        super().__init__(receiver, routes_list)
        self.matchers = matchers
        self.continue_ = continue_ or False


route = settings.get('route')
default_receiver = route.get('receiver')
routes = route.get('routes')
main_route = MainRoute(default_receiver, routes)


pass
