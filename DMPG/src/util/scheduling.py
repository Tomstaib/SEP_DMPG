from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from __future__ import absolute_import, division, print_function
import warnings
import pandas as pd
import tensorflow as tf
import numpy as np

from tf_agents.drivers import py_driver
from tf_agents.specs import tensor_spec
from tf_agents.utils import common
from tf_agents.replay_buffers import py_uniform_replay_buffer
from tf_agents.environments import py_environment
from tf_agents.specs import array_spec
from tf_agents.trajectories import time_step as ts
from src.util.dqn import create_agent

tf.random.set_seed(1)

warnings.simplefilter(action='ignore', category=FutureWarning)


class SchedulingEnv(py_environment.PyEnvironment):

    def __init__(self, source=None, products: pd.DataFrame = None, scheduling_period=100):
        self._action_spec = array_spec.BoundedArraySpec(
            shape=([]), dtype=np.int32, minimum=0, maximum=1, name='action'
        )

        self._observation_spec = tf.TensorSpec(shape=(3,), dtype=np.int32)
        self._reward_spec = tf.TensorSpec(shape=(), dtype=tf.float32)
        self._state = None     # , 0, 0, 0     # Current Number, Due_date, Number Scheduled
        self._episode_ended = False
        self.scheduling_period = scheduling_period
        self.products = products
        self.reward = 0
        self.source = source
        self.scheduling_finished = False
        self.current_index = 0
        self.number_scheduled = 0

    def reward_spec(self):
        return self._reward_spec

    def action_spec(self):
        return self._action_spec

    def observation_spec(self):
        return self._observation_spec

    def _reset(self):
        # self._state = np.array([0, self.source.env.now, self.source.number_products_last_period, 0])  # , 0, 0, 0
        self._state = np.array([int(self.source.get_queue_next_server()), 0, 0])
        self.current_index = 0
        self.scheduling_finished = False
        self._episode_ended = False
        self.number_scheduled = 0
        # self.reward = 0
        return ts.restart(np.array(self._state, dtype=np.int32))

    def product_iteration(self, action, max_num_prodicts=100):
        while True:
            self.current_index += 1
            if self.current_index == len(self.products) - 1 or action == 0:
                return True
            row = self.source.products.iloc[self.current_index + 1]
            if action == 1:
                if row['Scheduled'] is False:
                    self.source.products.at[self.current_index, 'Scheduled'] = True
                    self.source.schedule.loc[len(self.source.schedule)] = self.source.products.iloc[self.current_index]
                    # self.source.schedule = self.source.schedule.append(self.source.products.iloc[self.current_index])
                    self.number_scheduled += 1
                    return False

    def _step(self, action):
        if self.source is None:
            print("Undefinded source!")
        if self.products is None:
            print("Undefined products!")
        if self._episode_ended:
            return self._reset()
        if self.scheduling_finished:
            self._episode_ended = True
            self._state = np.array([int(self.source.get_queue_next_server()),
                                    0,
                                    int(self.source.calc_utilization_next_servers(reset_utilization=False))])
        else:
            self.scheduling_finished = self.product_iteration(action)
            self.products_scheduled = len(self.source.schedule)

            self._state = np.array([self.number_scheduled + int(self.source.get_queue_next_server()),
                                    1, 0])
        if self._episode_ended:
            reward = self.source.calc_reward()
            # print("state: ", self._state, "action: ", action.numpy().item(), "reward: ", reward)
            return ts.termination(
                np.array(self._state, dtype=np.int32), reward=reward)
        else:
            if action == 1:
                reward = 0
            else:
                reward = 0
            return ts.transition(
                np.array(self._state, dtype=np.int32), reward=reward, discount=1)


class Scheduler:

    def __init__(self, params):
        self.params = params
        self.env = SchedulingEnv()
        self.epsilon_scheduler = EpsilonScheduler()
        self.q_net = None

    def initialize(self):
        self.agent = create_agent(self.params, q_net=self.q_net, epsilon_greedy=self.epsilon_scheduler.get_epsilon())

        '''Defining the Replay Buffer'''
        replay_buffer_max_length = 32

        self.action_tensor_spec = tensor_spec.from_spec(self.env.action_spec())
        self.observation_tensor_spec = tensor_spec.from_spec(self.env.observation_spec())

        data_spec = self.agent.collect_data_spec    # tf.TensorSpec(self.agent.collect_data_spec)
        self.replay_buffer = py_uniform_replay_buffer.PyUniformReplayBuffer(
            capacity=replay_buffer_max_length,
            data_spec=tensor_spec.to_array_spec(data_spec)
        )
        self.agent.train = common.function(self.agent.train)
        self.agent.train_step_counter.assign(0)

        self.returns = []

        self.collect_driver = py_driver.PyDriver(
            self.env,
            self.agent.collect_policy,
            observers=[self.replay_buffer_observer],
            max_steps=1

        )

    def get_buffer_data(self, queue, num_experiences=32):
        for _ in range(num_experiences):
            queue.put(self.replay_buffer.get_next())
        data_spec = self.agent.collect_data_spec    # tf.TensorSpec(self.agent.collect_data_spec)
        self.replay_buffer = py_uniform_replay_buffer.PyUniformReplayBuffer(
            capacity=num_experiences,
            data_spec=tensor_spec.to_array_spec(data_spec))
        # TODO: Überarbeiten: Sicherstellen, dass alle gesammelten erfahrungen übergeben werden

    def replay_buffer_observer(self, _trajectory):
        self.replay_buffer.add_batch(_trajectory)

    def run(self):
        while True:
            time_step = self.env.reset()
            while not self.env.scheduling_finished:
                time_step = self.step(time_step)
            yield None
            time_step = self.step(time_step)
            yield None

    def step(self, time_step):
        time_step = tf.nest.map_structure(lambda x: tf.expand_dims(x, axis=0), time_step)
        time_step, _ = self.collect_driver.run(time_step)
        return time_step


class EpsilonScheduler:
    def __init__(self):
        self.epsilon = None

    def get_epsilon(self):
        return self.epsilon
