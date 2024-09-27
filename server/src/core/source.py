import logging
from typing import Union
import pandas as pd
from src.util.global_imports import ENTITY_PROCESSING_LOG_ENTRY
import src.util.global_imports as gi
from src.core.entity import Entity
from src.util.helper import get_value_from_distribution_with_parameters, validate_probabilities, create_connection_cache
from src.util.date_time import DateTime
from src.core.resetable_named_object import ResetAbleNamedObject, ResetAbleNamedObjectManager
from src.core.routing_object import RoutingObject
from src.core.model import Model, ComponentType


class Source(ResetAbleNamedObject, RoutingObject):
    """
    A source is a component that creates entities and routes them to the next component.
    """
    sources = ResetAbleNamedObjectManager()
    """
    A list of all the sources in the simulation.
    """

    def __init__(self, env, name, creation_time_distribution_with_parameters=None, arrival_table_path=None,
                 routing_expression=None, entity_class=Entity) -> None:
        """
        Create a source.

        :param env: SimPy environment
        :param name: Name of the source
        :param creation_time_distribution_with_parameters: Tuple of distribution function and parameters
        :param arrival_table_path: Path to the arrival table
        """
        super().__init__(env, name, Source.sources)
        Model().add_component(self, ComponentType.SOURCES)
        RoutingObject.__init__(self, env, routing_expression)
        self.creation_time_dwp = creation_time_distribution_with_parameters
        self.entity_class = entity_class

        if arrival_table_path:
            self.arrival_table = pd.read_csv(arrival_table_path)
            self.arrival_table_index = 1
            self.arrival_table_column_name = list(self.arrival_table.columns)[0]
        else:
            self.arrival_table = None
            self.arrival_table_index = None

        self.action = env.process(self.run())

        self.entities = []
        self.entities_created_pivot_table = 0
        self.number_exited_pivot_table = 0

    def reset(self):
        """
        Reset the source. Set the next_component and list of entities to an empty list and reset the entities created.
        """
        self.next_components = []
        self.entities_created_pivot_table = 0
        self.entities = []
        self.number_exited_pivot_table = 0

    def run(self):
        """
        Run the source.
        Create entities and route them to the next component.

        """
        validate_probabilities(self)
        create_connection_cache(self)

        while True:
            entity = self.entity_class(f"{self.name}_Entity_{self.entities_created_pivot_table}", self.env.now)
            if self.env.now >= gi.DURATION_WARM_UP:
                self.entities_created_pivot_table += 1
                self.number_exited_pivot_table += 1

            logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                "".join([self.name, " created ", entity.name]), DateTime.get(entity.creation_time)))

            self.entities.append(entity)
            self.route_entity(entity)

            wait_time = self.arrival_table_based_wait_time() if self.arrival_table is not None else (
                get_value_from_distribution_with_parameters(self.creation_time_dwp))

            yield self.env.timeout(wait_time)

    def arrival_table_based_wait_time(self) -> Union[int, float]:
        """
        Get the wait time from the arrival table and increment the index for the next wait time.

        :return: wait_time
        """
        wait_time = self.arrival_table.at[self.arrival_table_index, self.arrival_table_column_name] - self.env.now
        self.arrival_table_index += 1

        return wait_time

    def __repr__(self) -> str:
        """
        String representation of the source instance name

        :return: name
        """
        return self.name
