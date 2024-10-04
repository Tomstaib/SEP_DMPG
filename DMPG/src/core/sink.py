import logging
import src.util.global_imports as gi
from simpy import Environment

from src.core.entity import Entity
from src.util.global_imports import ENTITY_PROCESSING_LOG_ENTRY
from src.util.date_time import DateTime
from src.core.resetable_named_object import ResetAbleNamedObject, ResetAbleNamedObjectManager
from src.core.tally_statistic import TallyStatistic
from typing import Callable, Tuple, Any


class Sink(ResetAbleNamedObject):
    """Class variable to keep track of all sink instances"""
    sinks = ResetAbleNamedObjectManager()
    """list of all existing sinks instances"""

    def __init__(self, env: Environment, name: str, addon_processing_done_method_with_parameters=None) -> None:
        """
        Initialize a sink instance

        :param env (Environment): Reference to SimPy environment
        :param name (str): Name of the new sink
        :param addon_process_trigger: Callable to be executed as an add-on process trigger
        """
        super().__init__(env, name, Sink.sinks)
        # Model().add_component(self, ComponentType.SINKS)

        self.entities_processed = 0
        """Total number of entities processed by this sink."""
        self.total_time_in_system = 0
        """Total time spent by entities in the system while being processed by this sink."""
        self.max_time_in_system_pivot_table = 0
        """Maximum time any entity spent in the system while being processed by this sink."""
        self.min_time_in_system_pivot_table = float('inf')
        """Minimum time any entity spent in the system while being processed by this sink."""
        self.number_entered_pivot_table = 0
        """Total number of entities entered into this sink."""
        self.tally_statistic = TallyStatistic()
        """Callable method with parameters, called when entity processing is done."""
        self.addon_processing_done_method_with_parameters = addon_processing_done_method_with_parameters

        self.processed_entities = []

    def use_addon_process_trigger(self, entity: Entity, ptwp: Tuple[Callable[..., Any]]):
        process_trigger, parameters = ptwp[0], ptwp[1:]
        process_trigger(self, entity, *parameters)

    def reset(self):
        self.entities_processed = 0

    def handle_entity_arrival(self, entity: Entity) -> None:
        """
        This method updates various statistics related to entity processing, including the time spent by the entity
        in the system, the total number of entities processed by this sink, the maximum and minimum time any entity
        spent in the system, and the number of entities entered into this sink.

        :param entity: The entity to be processed
        """

        if self.env.now >= gi.DURATION_WARM_UP:
            time_in_system = self.env.now - entity.creation_time
            self.total_time_in_system += time_in_system
            self.max_time_in_system_pivot_table = max(self.max_time_in_system_pivot_table, time_in_system)
            self.min_time_in_system_pivot_table = min(self.min_time_in_system_pivot_table, time_in_system)

            self.number_entered_pivot_table += 1

        self.entities_processed += 1

        entity.destruction_time = self.env.now

        self.processed_entities.append(entity)

        if self.addon_processing_done_method_with_parameters:
            self.addon_processing_done_method_with_parameters[0](self, entity,
                                                                 *self.addon_processing_done_method_with_parameters[1:])

        logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
            "".join([self.name, " destroyed ", entity.name]), DateTime.get(self.env.now)))

    def __repr__(self) -> str:
        """
        String representation of the sink instance name

        :return: name
        """
        return self.name
