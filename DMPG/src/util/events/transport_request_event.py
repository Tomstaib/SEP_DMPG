from simpy import Event, Environment
from simpy.events import EventCallbacks


class TransportRequestEvent(Event):
    def __init__(
            self,
            env: Environment,
    ):
        self.env = env
        self.callbacks: EventCallbacks = []
        self._ok = True
