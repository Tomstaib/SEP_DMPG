import logging
import simpy
from functools import lru_cache

import src.util.global_imports as gi
from simpy import Event
from collections import deque
from src.core.entity import Entity
from src.core.entity import SubEntity
from src.util.global_imports import ENTITY_PROCESSING_LOG_ENTRY
from src.util.helper import get_value_from_distribution_with_parameters, validate_probabilities, round_value, \
    create_connection_cache
from src.core.queue_type import QueueType
from src.util.date_time import DateTime
from src.core.resetable_named_object import ResetAbleNamedObject, ResetAbleNamedObjectManager
from src.util.work_schedule import ask_work_schedule
from src.core.routing_object import RoutingObject
from src.core.model import Model, ComponentType


class Server(ResetAbleNamedObject, RoutingObject):
    """Represents a server in a simulation environment"""

    servers = ResetAbleNamedObjectManager()
    """List of all existing server instances"""

    def __init__(self, env: simpy.Environment, name: str,
                 processing_time_distribution_with_parameters=None, week=None,
                 time_between_machine_breakdowns=None,
                 machine_breakdown_duration=None,
                 queue_order: QueueType = QueueType.FIFO,
                 routing_expression=None):
        """
        Creates a server object which takes a simpy environment, and a name. You can optionally set parameters for
        distribution with a set processing time, a time between machine breakdowns, and a time for the duration of a
        machine breakdown. You can also set the queue ordering strategy which has a default value of 'FIFO'


       :param env: Defines the simpy environment in which a simulation could run.
       :param name: Name of the server instance.
       :param processing_time_distribution_with_parameters:
       :param time_between_machine_breakdowns: Time between machine breakdowns
       :param machine_breakdown_duration: Duration of the machine breakdown
       :param queue_order: FIFO or LIFO
       """
        super().__init__(env, name, Server.servers)
        Model().add_component(self, ComponentType.SERVERS)
        RoutingObject.__init__(self, env, routing_expression)
        self.week = week
        self.processing_time_dwp = processing_time_distribution_with_parameters
        self.time_between_machine_breakdowns = time_between_machine_breakdowns
        self.machine_breakdown_duration = machine_breakdown_duration
        self.queue_order = queue_order

        self.server_queue: deque = deque()  # changed from []
        """List which contains all entities that have been added to the server queue."""
        self.entities_processed = 0
        """Counter for how many entities are processed yet."""

        self.action = env.process(self.run())
        """The action that will be performed on the next component."""
        self.total_processing_time_pivot_table = 0
        """Counter for the total processing time."""

        self.number_entered_pivot_table = 0
        """Counter for the number of entered components."""
        self.number_exited_pivot_table = 0
        """Counter for the number of exited components."""
        self.units_allocated = 0
        """Counter for the number of units allocated."""
        self.units_utilized_pivot_table = 0
        """Counter for the number of units utilized."""
        self.start_processing_time = 0
        """Counter for the start processing time."""

        self.processing = env.event()
        self.total_downtime_pivot_table = 0
        """Counts the total downtime of all entities."""
        self.number_downtimes_pivot_table = 0
        self.uptime = 0
        self.total_uptime = 0
        self.number_uptimes = 0

        if self.time_between_machine_breakdowns:
            self.time_until_next_machine_breakdown = (
                get_value_from_distribution_with_parameters(self.time_between_machine_breakdowns))

    def reset(self):
        pass

    def is_available(self):
        """
        Checks if the server is available

        :return: True if available, False otherwise
        """
        return len(self.server_queue) == 0

    def process_entity(self, entity: Entity) -> None:
        """
        Processes an entity and adds it to the server queue

        :param entity: Entity to process
        """
        self.server_queue.append(entity)

        # activate processing if not activated
        if not self.processing.triggered:
            self.processing.succeed()
            (logging.root.level <= logging.TRACE and logging.trace(
                ENTITY_PROCESSING_LOG_ENTRY.format("".join([self.name, " starts processing"]),
                                                   DateTime.get(self.env.now))))
            self.uptime = self.env.now

    @lru_cache(maxsize=512)
    def run(self) -> Event:
        """
        Runs the queued entities while taking the queue order into consideration
        """
        validate_probabilities(self)
        create_connection_cache(self)

        trace_enabled = logging.root.level <= logging.TRACE

        while True:

            if self.week is not None:
                boolean, time_to_wait, value = ask_work_schedule(self.env.now, self.week)
            else:
                boolean = True
            if boolean:

                if self.server_queue:
                    if self.queue_order == QueueType.LIFO:
                        entity = self.server_queue.pop()
                    else:
                        entity = self.server_queue.popleft()  # changed from pop(0)

                    if trace_enabled:
                        logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                            "".join([self.name, " processing ", entity.name]), DateTime.get(self.env.now)))
                    # logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                    #     "".join([self.name, " processing ", entity.name]), DateTime.get(self.env.now)))

                    processing_time_start = self.env.now

                    processing_time = get_value_from_distribution_with_parameters(self.processing_time_dwp)

                    if self.env.now > gi.DURATION_WARM_UP:
                        self.units_utilized_pivot_table += processing_time
                        self.number_entered_pivot_table += 1

                    if not self.time_between_machine_breakdowns or processing_time < self.time_until_next_machine_breakdown:
                        yield self.env.timeout(processing_time)
                    else:
                        # processing until breakdown
                        yield self.env.timeout(self.time_until_next_machine_breakdown)
                        processing_time -= self.time_until_next_machine_breakdown  # process time remaining

                        if trace_enabled:
                            logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                                "".join([self.name, " failure at "]), DateTime.get(self.env.now)))
                        # logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                        #     "".join([self.name, " failure at "]), DateTime.get(self.env.now)))

                        # breakdown
                        self.time_until_next_machine_breakdown = (
                            get_value_from_distribution_with_parameters(self.time_between_machine_breakdowns))
                        breakdown_time = get_value_from_distribution_with_parameters(self.machine_breakdown_duration)

                        if self.env.now > gi.DURATION_WARM_UP:
                            self.total_downtime_pivot_table += breakdown_time
                            self.number_downtimes_pivot_table += 1

                        yield self.env.timeout(breakdown_time)

                        if trace_enabled:
                            logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                                "".join([self.name, " failure corrected at "]), DateTime.get(self.env.now)))
                        # logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                        #     "".join([self.name, " failure corrected at "]), DateTime.get(self.env.now)))

                        # continue processing after breakdown
                        yield self.env.timeout(processing_time)

                    if trace_enabled:
                        logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                            "".join([self.name, " processing ", entity.name, " done, time ",
                                     str(round_value(self.env.now - processing_time_start))]),
                            DateTime.get(self.env.now)))
                    # logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                    #    "".join([self.name, " processing ", entity.name, " done, time ",
                    #             str(round_value(self.env.now - processing_time_start))]), DateTime.get(self.env.now)))

                    if self.env.now > gi.DURATION_WARM_UP:
                        self.total_processing_time_pivot_table += processing_time  # Accumulate total processing time
                        self.entities_processed += 1
                        self.number_exited_pivot_table += 1

                    if isinstance(entity, SubEntity):
                        entity.count_processing()
                        entity.add_to_server_history(self.name)

                    self.route_entity(entity)
                else:
                    # deactivate processing
                    self.processing = self.env.event()
                    self.uptime = self.env.now - self.uptime
                    self.total_uptime += self.uptime
                    self.number_uptimes += 1

                    if trace_enabled:
                        logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                            "".join([self.name, " stops processing, uptime ",
                                     DateTime.get(self.uptime, time_string_from_initial_date=False),
                                     ", total uptime ",
                                     DateTime.get(self.total_uptime, time_string_from_initial_date=False),
                                     " (", "0" if self.env.now == 0 else
                                     str(round_value(self.total_uptime / self.env.now * 100)),
                                     " %), avg uptime ",
                                     DateTime.get(self.total_uptime / self.number_uptimes,
                                                  time_string_from_initial_date=False)]),
                            DateTime.get(self.env.now)))
                    """logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                        "".join([self.name, " stops processing, uptime ",
                                 DateTime.get(self.uptime, time_string_from_initial_date=False),
                                 ", total uptime ", DateTime.get(self.total_uptime, time_string_from_initial_date=False),
                                 " (", "0" if self.env.now == 0 else
                                 str(round_value(self.total_uptime / self.env.now * 100)),
                                 " %), avg uptime ",
                                 DateTime.get(self.total_uptime / self.number_uptimes,
                                              time_string_from_initial_date=False)]),
                        DateTime.get(self.env.now)))"""

                    yield self.processing
            else:
                yield self.env.timeout(time_to_wait)

    def __repr__(self):
        """Returns the name of the object when called by the Print function."""
        return self.name
