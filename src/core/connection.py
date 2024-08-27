import logging
from simpy import Environment
from collections import deque

from src.core.entity import Entity
from src.util.global_imports import ENTITY_PROCESSING_LOG_ENTRY
from src.util.date_time import DateTime
from src.core.resetable_named_object import ResetAbleNamedObject, ResetAbleNamedObjectManager
from src.core.routing_object import RoutingObject


class Connection(ResetAbleNamedObject, RoutingObject):
    connections = ResetAbleNamedObjectManager()

    def __init__(self, env: Environment, origin_component, next_component, name: str, process_duration: float = None, probability: float = None):
        super().__init__(env, name, Connection.connections)
        RoutingObject.__init__(self, env)

        self.probability = probability
        self.entities_processed = 0
        self.number_entered = 0
        self.entities_queue = deque()  # changed from []
        self.origin_component = origin_component
        self.next_component = next_component
        self.processing = env.event()
        self.process_duration = process_duration
        self.action = env.process(self.run())

    def reset(self):
        self.entities_processed = 0
        self.entities_queue.clear()

    def process_entity(self, entity: Entity):
        self.entities_queue.append(entity)

        if not self.processing.triggered:
            self.processing.succeed()

    def run(self):
        while True:
            if self.entities_queue:
                entity = self.entities_queue.popleft()  # changed from pop(0)
                self.number_entered += 1

                if self.process_duration:
                    yield self.env.timeout(self.process_duration)

                self.processing = self.env.event()

                self.log_and_process(self.origin_component, self.next_component, entity)
                self.entities_processed += 1

                yield self.processing
            else:
                self.processing = self.env.event()
                yield self.processing

    @staticmethod
    def log_and_process(component, next_component, entity: Entity):
        logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
            "".join([component.name, " added ", entity.name, " to ", next_component.name]),
            DateTime.get(component.env.now)))
        next_component.process_entity(entity)
        component.number_exited += 1

    def __repr__(self):
        return self.name
