import logging

import simpy
from simpy import Event

import src.util.global_imports as gi
from src.core.entity import Entity, SubEntity
from src.core.model import Model, ComponentType
from src.core.queue_type import QueueType
from src.util.global_imports import ENTITY_PROCESSING_LOG_ENTRY
from src.core.resetable_named_object import ResetAbleNamedObject, ResetAbleNamedObjectManager
from src.core.routing_object import RoutingObject
from src.util.date_time import DateTime
from src.util.helper import get_value_from_distribution_with_parameters, round_value, validate_probabilities, \
    create_connection_cache
from src.util.work_schedule import ask_work_schedule


class Combiner(ResetAbleNamedObject, RoutingObject):
    """Represents a combiner in a simulation environment"""

    combiners = ResetAbleNamedObjectManager()
    """List of all existing combiner instances"""

    def __init__(self, env: simpy.Environment, name: str,
                 processing_time_distribution_with_parameters=None,
                 capacity=1,
                 time_between_machine_breakdowns=None,
                 machine_breakdown_duration=None,
                 work_schedule=None,
                 queue_order: QueueType = QueueType.FIFO,
                 routing_expression=None, members_to_combine=1):
        """
        Creates a combiner object which takes a simpy environment, and a name. You can optionally set parameters for
        distribution with a set processing time, a time between machine breakdowns, and a time for the duration of a
        machine breakdown. You can also set the queue ordering strategy which has a default value of 'FIFO'

       :param env: simpy environment
       :param name: combiner identification for logging / pivot table
       :param processing_time_distribution_with_parameters:
       :param time_between_machine_breakdowns: Time between machine breakdowns
       :param machine_breakdown_duration: Duration of the machine breakdown
       :param queue_order: e.g., FIFO
       """
        super().__init__(env, name, Combiner.combiners)
        Model().add_component(self, ComponentType.COMBINER)
        RoutingObject.__init__(self, env, routing_expression)

        self.week = work_schedule
        self.processing_time_dwp = processing_time_distribution_with_parameters
        self.time_between_machine_breakdowns = time_between_machine_breakdowns
        self.machine_breakdown_duration = machine_breakdown_duration
        self.queue_order = queue_order

        self.entities_processed = 0
        """Counter for how many entities are processed yet."""

        self.action = env.process(self.run())
        """The action that will be performed on the next component."""
        self.total_processing_time_pivot_table = 0
        """Counter for the total processing time."""

        self.number_entered_parent_pivot_table = 0
        self.number_entered_member_pivot_table = 0
        """Counter for the number of entered components."""
        self.number_exited_parent_pivot_table = 0
        self.number_exited_member_pivot_table = 0
        """Counter for the number of exited components."""
        self.units_allocated = 0
        """Counter for the number of units allocated."""
        self.units_utilized_pivot_table = 0
        """Counter for the number of units utilized."""
        self.start_processing_time = 0
        """Counter for the start processing time."""
        self.capacity = capacity  #
        """New attribute for combiner's capacity."""
        self.currently_processing = []  #
        """Track currently processing entities."""

        self.processing = env.event()
        self.total_downtime_pivot_table = 0
        """Counts the total downtime of the Server."""
        self.number_downtimes_pivot_table = 0
        """Counts the total amount downtime of the Server."""
        self.uptime = 0
        self.total_uptime = 0
        self.number_uptimes = 0

        self.connection_cache = {}

        self.initialized = False
        self.units_utilized_over_time = []

        self.parent_queue = []
        self.member_queue = []

        self.members_to_combine = members_to_combine

        if self.time_between_machine_breakdowns:
            self.time_until_next_machine_breakdown = (
                get_value_from_distribution_with_parameters(self.time_between_machine_breakdowns))

    def reset(self):
        self.parent_queue.clear()
        self.member_queue.clear()
        self.currently_processing.clear()

    def is_available(self):
        """
        Checks if the combiner is available.

        :return: True if available, False otherwise
        """
        return len(self.parent_queue) == 0 or len(self.member_queue) == 0

    def _try_process_from_queue(self):
        """
        If there's capacity, start processing the next entity in the queue,
        while taking the queue order into consideration.
        """
        if self.parent_queue and self.member_queue and len(self.currently_processing) < self.capacity:
            if self.queue_order == QueueType.LIFO:
                parent: Entity = self.parent_queue.pop()
            else:  # FIFO
                parent: Entity = self.parent_queue.pop(0)

            for i in range(0, self.members_to_combine):
                if self.queue_order == QueueType.LIFO:
                    entity = self.member_queue.pop()
                    parent.batch_members.append(entity)
                else:  # FIFO
                    entity = self.member_queue.pop(0)
                    parent.batch_members.append(entity)

            self.currently_processing.append(parent)
            self.env.process(self._process_entity_logic(parent))

    def handle_entity_arrival(self, entity: Entity) -> None:
        """
        Processes an entity and adds it to the parent or member queue.

        :param entity: entity to process
        """

        if self.env.now >= gi.DURATION_WARM_UP:
            if entity.is_parent:
                self.number_entered_parent_pivot_table += 1
            else:
                self.number_entered_member_pivot_table += 1

        if entity.is_parent:
            self.parent_queue.append(entity)
        else:
            self.member_queue.append(entity)

        # activate processing if not activated
        if not self.processing.triggered:
            self.processing.succeed()
            (logging.root.level <= logging.TRACE and logging.trace(
                ENTITY_PROCESSING_LOG_ENTRY.format("".join([self.name, " starts processing"]),
                                                   DateTime.get(self.env.now))))
            self.uptime = self.env.now

    def _handle_machine_breakdown(self, processing_time):
        """
        Steps to handle machine breakdown:
        (1) Process until breakdown
        (2) Breakdown
        """
        if processing_time > self.time_until_next_machine_breakdown:
            # (1) process until breakdown
            yield self.env.timeout(self.time_until_next_machine_breakdown)

            logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                "".join([self.name, " failure at "]), DateTime.get(self.env.now)))

            # (2) Breakdown
            breakdown_duration = get_value_from_distribution_with_parameters(self.machine_breakdown_duration)
            yield self.env.timeout(breakdown_duration)

            # (3) Update downtime statistics
            if self.env.now >= gi.DURATION_WARM_UP:
                self.number_downtimes_pivot_table += 1
                self.total_downtime_pivot_table += breakdown_duration

            logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                "".join([self.name, " failure corrected at "]), DateTime.get(self.env.now)))

            # (4) Continue processing after breakdown is resolved
            processing_time_remaining = processing_time - self.time_until_next_machine_breakdown
            self.time_until_next_machine_breakdown = \
                (get_value_from_distribution_with_parameters(self.time_between_machine_breakdowns))
            yield self.env.timeout(processing_time_remaining)

        else:
            yield self.env.timeout(processing_time)
            self.time_until_next_machine_breakdown -= processing_time

    def _process_entity_logic(self, entity):
        """
        Logic to process an entity, considering processing time.
        This is a generator function used by SimPy's process management.
        """
        start_time = self.env.now

        processing_time = get_value_from_distribution_with_parameters(self.processing_time_dwp)

        if self.time_between_machine_breakdowns is None:
            yield self.env.timeout(processing_time)
        else:
            yield from self._handle_machine_breakdown(processing_time)

        logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
            "".join([self.name, " processing ", entity.name, " done, time ",
                     str(round_value(self.env.now - start_time))]), DateTime.get(self.env.now)))

        end_time = self.env.now

        # Update utilization records
        if end_time >= gi.DURATION_WARM_UP:
            self.units_utilized_over_time.append((start_time, end_time, len(self.currently_processing)))

            self.entities_processed += 1
            self.total_processing_time_pivot_table += processing_time

            self.number_exited_parent_pivot_table += 1
            for memeber in entity.batch_members:
                self.number_exited_member_pivot_table += 1

        # After processing, remove entity from list of currently processing entities
        self.currently_processing.remove(entity)

        # Log completion of processing
        logging.root.level <= logging.TRACE and logging.trace(
            ENTITY_PROCESSING_LOG_ENTRY.format("".join([self.name, " finished processing ", entity.name]),
                                               DateTime.get(end_time)))

        if isinstance(entity, SubEntity):
            entity.count_processing()
            entity.add_to_combiner_history(self.name)

        entity.current_location = self
        # Handle connections to next components
        self.route_entity(entity)

        if not self.week:
            self._try_process_from_queue()

    def run(self) -> Event:
        """
        Runs the queued entities while taking the queue order into consideration
        """
        if not self.initialized:
            self._initialize_combiner()
            self.initialized = True
        while True:
            # Handle work schedule
            active, time_to_wait, _ = ask_work_schedule(self.env.now, self.week) if self.week else (True, 0, None)

            if active:
                # Check if there's any entity currently being processed and if there's space for more
                if (self.parent_queue or self.members_to_combine) and len(self.currently_processing) < self.capacity:
                    self._try_process_from_queue()

                # If there's nothing to process or the combiner can't combine anything, wait for the next trigger
                if not (self.parent_queue and self.member_queue) or self.members_to_combine == 0 or len(
                        self.currently_processing) == self.capacity:
                    yield self.processing
                    self.processing = self.env.event()  # Reset the event for the next round
            else:
                yield self.env.timeout(time_to_wait)

    def _initialize_combiner(self):
        """Perform initial setup tasks for the combiner, including validating probabilities."""
        validate_probabilities(self)
        create_connection_cache(self)

    def __repr__(self):
        """Returns the name of the object when called by the Print function."""
        return self.name
