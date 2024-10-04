from simpy import Environment
from simpy.events import Event, EventCallbacks


class StorageEvent(Event):

    def __init__(
            self,
            env: Environment,
    ):
        self.env = env
        self.callbacks: EventCallbacks = []
        self._ok = True
