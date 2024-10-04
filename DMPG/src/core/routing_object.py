from src.core.entity import Entity
from src.util.global_imports import random


class RoutingObject:

    def __init__(self, env, routing_expression=None):
        self.env = env
        self.routing_expression = routing_expression
        self.next_components = []  # TODO: to be deleted?
        self.number_exited = 0
        self.connection_cache = {}
        self.connections = {}

    def route_entity(self, entity: Entity):
        if self.routing_expression:
            self.routing_expression[0](self, entity, *self.routing_expression[1:])
        else:
            decision = random.uniform(0, 100)
            for cumulative_probability in self.connection_cache:
                if decision <= cumulative_probability:
                    next_server_via = self.connection_cache[cumulative_probability]
                    next_server_via.handle_entity_arrival(entity)
                    break

    def connect(self, next_server, probability: float = None, travel_duration: float = None):
        from src.core.source import Source  # circular import workaround
        from src.core.connection import Connection
        if isinstance(next_server, Source):
            raise ValueError("Next component must be a Server or Sink")
        self.next_components.append((next_server, probability))  # TODO: to be replaced by connections?
        self.connections[next_server.name] = Connection(self.env, self, next_server, next_server.name, travel_duration, probability)
