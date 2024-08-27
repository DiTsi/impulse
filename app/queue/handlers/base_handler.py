from abc import ABC, abstractmethod


class BaseHandler(ABC):
    """
    Base class for all handlers

    :param queue: Queue instance
    :param application: Application instance
    :param incidents: Incidents instance
    """
    __slots__ = ['queue', 'app', 'incidents']

    def __init__(self, queue, application, incidents):
        self.queue = queue
        self.app = application
        self.incidents = incidents

    @abstractmethod
    def handle(self, *args, **kwargs):
        pass
