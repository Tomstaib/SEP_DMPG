import logging
from typing import Union

from src.util.events.waiting_event import WaitingEvent
from src.util.global_imports import ENTITY_PROCESSING_LOG_ENTRY
import src.util.global_imports as gi

from src.util.helper import create_connection_cache
from src.util.date_time import DateTime
from src.core.resetable_named_object import ResetAbleNamedObject, ResetAbleNamedObjectManager
from src.core.routing_object import RoutingObject
from src.core.model import Model, ComponentType
import pandas as pd
import tensorflow as tf
import pickle

from src.util.scheduling import Scheduler
from src.core.entity import Entity
from src.util.helper import get_value_from_distribution_with_parameters, validate_probabilities


class Source(ResetAbleNamedObject, RoutingObject):
    """
    A source is a component that creates entities and routes them to the next component.
    """
    sources = ResetAbleNamedObjectManager()
    """
    A list of all the sources in the simulation.
    """

    def __init__(self, env, name, creation_time_distribution_with_parameters=None, arrival_table_path=None,
                 routing_expression=None, entity_class=Entity, max_arrival: int = None) -> None:
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
            self.arrival_table = pd.read_csv(arrival_table_path, sep=';')
            self.arrival_table_index = 0
            self.arrival_table_column_name = list(self.arrival_table.columns)[0]
        else:
            self.arrival_table = None
            self.arrival_table_index = None

        self.action = env.process(self.run())

        self.entities = []
        self.entities_created_pivot_table = 0
        self.number_exited_pivot_table = 0

        self.max_arrival = max_arrival

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

            if self.entities_created_pivot_table == self.max_arrival:
                yield WaitingEvent(self.env)

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


class RL_Source(Source):
    def __init__(self, env, name, params, products=None):
        super().__init__(env, name)
        self.params = params
        if not products:
            self.products = self.generate_test_products()
        else:
            self.products = products
        self.scheduling_period = 100
        self.schedule = pd.DataFrame(columns=['ID', 'Due Date', 'Scheduled'])

        self.scheduling_finished = False
        self.scheduler = Scheduler(params)
        self.scheduler.env.source = self
        self.scheduler.env.products = self.products
        self.iterator = self.scheduler.run()

    def generate_test_products(self):
        products = []
        for i in range(50):
            products.append([i, i * 4, False])  # ID, due_date, Scheduled?
        products = pd.DataFrame(products, columns=['ID', 'Due Date', 'Scheduled'])
        return products

    def get_queue_next_server(self):
        number_units_in_queue = len(self.connections["Server"].next_component.server_queue)
        return number_units_in_queue

    def calc_utilization_next_servers(self, reset_utilization=True):
        utilization = self.connections["Server"].next_component.get_utilization_last_scheduling_period(reset_utilization)
        return utilization

    def calc_reward(self, target_utilization=80, tolerierte_ueberstunden=0.1):
        utilization = self.calc_utilization_next_servers()
        if utilization > target_utilization:     # * (1 + tolerierte_ueberstunden) or utilization == 0:
            reward = 0
        # elif target_utilization <= utilization <= target_utilization * (1 + tolerierte_ueberstunden):
        #     reward = target_utilization
        else:
            reward = utilization    # target_utilization / (target_utilization - utilization)
        return reward

    def scheduled_wait_time(self):
        next(self.iterator)
        if not self.scheduling_finished:
            self.scheduling_finished = True
            return self.scheduling_period
        else:
            self.scheduling_finished = False
            return 0

    def run(self):
        validate_probabilities(self)
        create_connection_cache(self)
        while True:
            wait_time = self.scheduled_wait_time()
            while not self.schedule.empty:
                self.schedule = self.schedule.iloc[1:, :]
                entity = self.entity_class(f"{self.name}_Entity_{self.entities_created_pivot_table}", self.env.now)

                logging.root.level <= logging.TRACE and logging.trace(ENTITY_PROCESSING_LOG_ENTRY.format(
                    "".join([self.name, " created ", entity.name]), DateTime.get(entity.creation_time)))
                self.entities.append(entity)
                self.route_entity(entity)
                if self.env.now > gi.DURATION_WARM_UP:
                    self.entities_created_pivot_table += 1
            yield self.env.timeout(wait_time)

    def save_agent(self, path='agent'):
        q_net = self.scheduler.agent._q_network
        tf.saved_model.save(q_net, 'agent')
        with open('replay_buffer.pkl', 'wb') as f:
            buffer_data = []
            for i in range(self.scheduler.replay_buffer.capacity):
                buffer_data.append(self.scheduler.replay_buffer.as_dataset())
            pickle.dump(buffer_data, f)
        print("Q-Net and Replay Buffer saved")
