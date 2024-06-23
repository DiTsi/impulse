from app.logger import logger
from app.route.route import MainRoute


def generate_route(route_dict):
    logger.debug(f'Creating Route')
    main_channel_name = route_dict['channel']
    main_chain = route_dict.get('chain')
    routes = route_dict.get('routes')

    route_ = MainRoute(main_channel_name, main_chain, routes)
    logger.debug(f'Route created')
    return route_
