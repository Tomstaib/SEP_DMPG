import sys
import os
import logging
import simpy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../VerteilteBerechnungen')))

from VerteilteBerechnungen.core.entity import Entity
from VerteilteBerechnungen.util.global_imports import random, ENTITY_PROCESSING_LOG_ENTRY
from VerteilteBerechnungen.util.helper import get_value_from_distribution_with_parameters, validate_probabilities, round_value, \
    create_connection_cache
from VerteilteBerechnungen.core.queue_type import QueueType
from VerteilteBerechnungen.util.date_time import DateTime


class Server:
    servers = []

    def __init__(self, env: simpy.Environment, name: str,
                 processing_time_distribution_with_parameters=None,
                 time_between_machine_breakdowns=None,
                 machine_breakdown_duration=None,
                 queue_order: QueueType = QueueType.FIFO):

        self.env = env
        self.name = name
        self.processing_time_dwp = processing_time_distribution_with_parameters
        self.time_between_machine_breakdowns = time_between_machine_breakdowns
        self.machine_breakdown_duration = machine_breakdown_duration
        self.queue_order = queue_order

        self.server_queue = []
        self.entities_processed = 0
        self.next_component = []

        self.action = env.process(self.run())
        self.total_processing_time = 0

        self.number_entered = 0
        self.number_exited = 0
        self.units_allocated = 0
        self.units_utilized = 0
        self.start_processing_time = 0

        self.processing = env.event()
        self.total_downtime = 0
        self.number_downtimes = 0
        self.uptime = None
        self.total_uptime = 0
        self.number_uptimes = 0

        self.connection_cache = {}

        if self.time_between_machine_breakdowns:
            self.time_until_next_machine_breakdown = (
                get_value_from_distribution_with_parameters(self.time_between_machine_breakdowns))

        Server.servers.append(self)

    @classmethod
    def reset_all(cls):
        for server in cls.servers:
            server.reset()

    def reset(self):
        pass

    def is_available(self):
        return len(self.server_queue) == 0

    def process_entity(self, entity: Entity):
        self.server_queue.append(entity)

        # activate processing if not activated
        if not self.processing.triggered:
            self.processing.succeed()
            (logging.root.level <= logging.TRACE and logging.trace(
                ENTITY_PROCESSING_LOG_ENTRY.format("".join([self.name, " starts processing"]),
                                                   DateTime.get(self.env.now))))
            self.uptime = self.env.now

    def connect(self, next_component, probability: float = None):
        self.next_component.append((next_component, probability))

    def run(self):
        validate_probabilities(self)
        create_connection_cache(self)

        while True:
            if self.server_queue:
                # Choose entity based on queue order
                if self.queue_order == QueueType.LIFO:
                    entity = self.server_queue.pop()
                else:
                    entity = self.server_queue.pop(0)  # default: FIFO

                self.number_entered += 1

                logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                    "".join([self.name, " processing ", entity.name]), DateTime.get(self.env.now)))

                processing_time_start = self.env.now

                processing_time = get_value_from_distribution_with_parameters(self.processing_time_dwp)
                self.units_utilized += processing_time

                if not self.time_between_machine_breakdowns or processing_time > self.time_until_next_machine_breakdown:
                    yield self.env.timeout(processing_time)
                else:
                    # processing until breakdown
                    yield self.env.timeout(self.time_until_next_machine_breakdown)
                    processing_time -= self.time_until_next_machine_breakdown       # process time remaining

                    logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                        "".join([self.name, " failure at "]), DateTime.get(self.env.now)))

                    # breakdown
                    self.time_until_next_machine_breakdown = (
                        get_value_from_distribution_with_parameters(self.time_between_machine_breakdowns))
                    breakdown_time = get_value_from_distribution_with_parameters(self.machine_breakdown_duration)
                    self.total_downtime += breakdown_time
                    self.number_downtimes += 1
                    yield self.env.timeout(breakdown_time)

                    logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                        "".join([self.name, " failure corrected at "]), DateTime.get(self.env.now)))

                    # continue processing after breakdown
                    yield self.env.timeout(processing_time)

                logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                    "".join([self.name, " processing ", entity.name, " done, time ",
                             str(round_value(self.env.now - processing_time_start))]), DateTime.get(self.env.now)))

                self.total_processing_time += processing_time  # Accumulate total processing time
                self.entities_processed += 1
                self.number_exited += 1
                self.connection(entity, processing_time)
            else:
                # deactivate processing
                self.processing = self.env.event()
                self.uptime = self.env.now - self.uptime
                self.total_uptime += self.uptime
                self.number_uptimes += 1

                logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                    "".join([self.name, " stops processing, uptime ",
                             DateTime.get(self.uptime, from_initial_date=False),
                             ", total uptime ", DateTime.get(self.total_uptime, from_initial_date=False),
                             " (", str(round_value(self.total_uptime / self.env.now * 100)),
                             " %), avg uptime ",
                             DateTime.get(self.total_uptime / self.number_uptimes, from_initial_date=False)]),
                    DateTime.get(self.env.now)))

                yield self.processing

    def connection(self, entity: Entity, processing_time):
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
