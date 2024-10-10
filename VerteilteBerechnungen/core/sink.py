import sys
import os
import logging
from simpy import Environment

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../VerteilteBerechnungen')))

from VerteilteBerechnungen.core.entity import Entity
from VerteilteBerechnungen.util.global_imports import ENTITY_PROCESSING_LOG_ENTRY
from VerteilteBerechnungen.util.date_time import DateTime


class Sink:
    all_sinks = []

    def __init__(self, env: Environment, name: str):
        self.env = env
        self.name = name

        self.entities_processed = 0
        self.total_time_in_system = 0
        self.max_time_in_system = 0
        self.min_time_in_system = float('inf')
        self.number_entered = 0

        Sink.all_sinks.append(self)

    @classmethod
    def reset_all(cls):
        for sink in cls.all_sinks:
            sink.reset()

    def reset(self):
        self.entities_processed = 0

    def process_entity(self, entity: Entity):
        time_in_system = self.env.now - entity.creation_time

        self.total_time_in_system += time_in_system
        self.max_time_in_system = max(self.max_time_in_system, time_in_system)
        self.min_time_in_system = min(self.min_time_in_system, time_in_system)

        self.entities_processed += 1
        self.number_entered += 1

        entity.destruction_time = self.env.now

        logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
            "".join([self.name, " destroyed ", entity.name]), DateTime.get(self.env.now)))

    def __repr__(self):
        return self.name
