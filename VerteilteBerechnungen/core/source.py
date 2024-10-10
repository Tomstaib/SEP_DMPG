import sys
import os
import logging
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../VerteilteBerechnungen')))

from util.global_imports import random, ENTITY_PROCESSING_LOG_ENTRY
from core.server import Server
from core.entity import Entity
from util.helper import get_value_from_distribution_with_parameters, validate_probabilities, create_connection_cache
from util.date_time import DateTime


class Source:
    sources = []

    def __init__(self, env, name, creation_time_distribution_with_parameters=None, arrival_table_path=None):
        self.env = env
        self.name = name
        self.creation_time_dwp = creation_time_distribution_with_parameters

        if arrival_table_path:
            self.arrival_table = pd.read_csv(arrival_table_path)
            self.arrival_table_index = 1
            self.arrival_table_column_name = list(self.arrival_table.columns)[0]
        else:
            self.arrival_table = None
            self.arrival_table_index = None

        self.next_component = []

        self.action = env.process(self.run())

        self.entities = []
        self.entities_created = 0
        self.number_exited = 0

        self.connection_cache = {}

        Source.sources.append(self)

    @classmethod
    def reset_all(cls):
        for source in cls.sources:
            source.reset()

    def reset(self):
        self.next_component = []
        self.entities_created = 0
        self.entities = []  # Reset the list of entities
        self.number_exited = 0

    def connect(self, next_server: Server, probability: float = None):
        if not isinstance(next_server, Server):
            raise ValueError("Next component must be a Server")
        self.next_component.append((next_server, probability))

    def run(self):
        validate_probabilities(self)
        create_connection_cache(self)

        while True:
            entity = Entity(f"{self.name}_Entity_{self.entities_created}", self.env.now)
            logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                "".join([self.name, " created ", entity.name]), DateTime.get(entity.creation_time)))
            self.entities.append(entity)
            self.route_entity(entity)
            self.entities_created += 1

            wait_time = self.arrival_table_based_wait_time() if self.arrival_table is not None else (
                get_value_from_distribution_with_parameters(self.creation_time_dwp))

            yield self.env.timeout(wait_time)

    def arrival_table_based_wait_time(self):
        wait_time = self.arrival_table.at[self.arrival_table_index, self.arrival_table_column_name] - self.env.now
        self.arrival_table_index += 1

        return wait_time

    def route_entity(self, entity: Entity):
        decision = random.uniform(0, 100)

        for cumulative_probability in self.connection_cache:
            if decision <= cumulative_probability:
                next_server = self.connection_cache[cumulative_probability]
                logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                    "".join([self.name, " added ", entity.name, " to ", next_server.name]), DateTime.get(self.env.now)))
                next_server.process_entity(entity)
                self.number_exited += 1
                break

    def __repr__(self):
        return self.name
