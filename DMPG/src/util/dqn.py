import os
import platform
import time
from datetime import datetime
import tensorflow as tf
import math

from setproctitle import setproctitle

tf.random.set_seed(1)


def create_dense_layer(num_units):
    '''
    Creates and returns a Dense layer with given number of units.
    This layer will be equipped with relu activation and a VarianceScaling kernel initializer.

    Args:
    num_units : int
        number of units (neurons) in the Dense layer
    '''
    import tensorflow as tf
    return tf.keras.layers.Dense(
        num_units,
        activation=tf.keras.activations.relu,
        kernel_initializer=tf.keras.initializers.VarianceScaling(
            scale=2.0, mode='fan_in', distribution='truncated_normal'))


def create_q_values_layer(num_actions):
    '''
    Creates and returns a Dense layer designed for representing Q-values.

    Args:
    num_actions : int
        the number of possible actions
    '''
    import tensorflow as tf
    return tf.keras.layers.Dense(
        num_actions,
        activation=None,
        kernel_initializer=tf.keras.initializers.RandomUniform(minval=-0.03, maxval=0.03),
        bias_initializer=tf.keras.initializers.Constant(-0.2))


def create_dqn_agent(env, q_network, optimizer, epsilon_greedy):
    '''
    Creates and initializes a DQN agent.

    Args:
    env : gym.Env
        the environment in which the agent will act.
    q_network : keras.Model
        the network that approximates Q-value function
    learning_rate : float
        learning rate for the Adam optimizer
    optimizer : keras.optimizers.Optimizer
        optimizer for training Q-network
    '''
    from tf_agents.agents.dqn import dqn_agent
    import tensorflow.keras as keras
    import tensorflow as tf
    train_step_counter = tf.Variable(0)
    agent = dqn_agent.DqnAgent(
        env.time_step_spec(),
        env.action_spec(),
        epsilon_greedy=epsilon_greedy,
        q_network=q_network,
        optimizer=optimizer,
        td_errors_loss_fn=keras.losses.Huber(),
        train_step_counter=train_step_counter)
    agent.initialize()
    return agent


def create_agent(params, epsilon_greedy, q_net=None, optimizer=None):
    '''
    This function creates and returns a DQN (Deep Q-Network) agent trained on a scheduling environment.

    Arguments:
    - params: A named tuple consisting of the following field:
      -- num_actions: The total number of possible actions in the environment.
      -- fc_layer_params: A list containing the numbers of units in each Dense layer.
      -- learning_rate: The learning rate for the Adam optimizer.
      -- env: The environment in which the agent will operate.
    - q_net: An existing Q-Network. If None, a new one will be created.
    - optimizer: An existing optimizer. If None, a new Adam optimizer will be created.

    The agent's Q-function is approximated using a neural network comprised of Dense layers.
    '''
    from tf_agents.networks import sequential
    import tensorflow as tf
    num_actions = params[0]
    fc_layer_params = params[1]
    learning_rate = params[2]
    env = params[3]

    # if no existing q_net is provided, create a new one
    if not q_net:
        # Initialize the Dense layers for the q_net
        dense_layers = [create_dense_layer(num_units) for num_units in fc_layer_params]
        # Initialize the Q-values layer
        q_values_layer = create_q_values_layer(num_actions)
        # Combine Dense and Q-values layers to create a Sequential Q-Network
        q_net = sequential.Sequential(dense_layers + [q_values_layer])

    # if no existing optimizer is provided, create a new one
    if not optimizer:
        if platform.system() == 'Darwin':
            optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
        else:
            optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)

    # Create and return the DQN agent using the environment, Q-Network, and optimizer
    return create_dqn_agent(env, q_net, optimizer, epsilon_greedy)


# Main training function
def train_process(q_net, q_buffer_agent, q_new_network, epsilon, q_losses, params,
                  update_interval=100, epsilon_decay=0.001, print_interval=100):
    setproctitle('train-process')
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    agent = create_agent(params, epsilon.value)  # Create a new agent

    # agent._q_network = q_net  # Assign q_net to the agent
    agent.initialize()  # Initialize the agent
    train_step = 0

    # Begin the training loop
    while True:
        try:
            # printer.print_message(f"Train Process still active. Train Step: {train_step}, epsilon: {epsilon.value}")
            train_step += 1
            # Updating epsilon value using exponential decay
            epsilon.value = max(math.exp(-train_step / 200), 0.1 - (0.1 / 3000) * train_step, 1 / 1000)    # , 0.3 - (0.3 / 1000 * train_step)
            # Training loop
            for episode in range(update_interval):
                values = q_buffer_agent.get()  # Get buffer data
                # Stack tensor and convert to batch
                sample_batch = tf.nest.map_structure(lambda t: tf.stack(t * 1), values)
                # Train the agent and accumulate the loss
                q_losses.put(agent.train(sample_batch).loss.numpy())
            # Notify workers
            notify_workers(q_new_network, agent, params)
            tf.keras.backend.clear_session()
            # print(f"Train Process still active. Train Step: {train_step}, epsilon: {epsilon.value}")
        except Exception as e:
            print(f"An error occurred: {e}")


# Calculate average loss function
def calculate_average_loss(current_loss, print_interval, average_loss):
    return average_loss + current_loss / print_interval


# Notify workers function
def notify_workers(q_new_network, agent, params):
    for worker in range(1):
        if q_new_network.full():
            print("Queue Agent to Worker is full")
        else:
            q_new_network.put(clone_network(agent, params))


def clone_network(agent, params):
    import tensorflow as tf
    env = params[3]
    # env = scheduling.SchedulingEnv()
    cloned_q_net = tf.keras.models.clone_model(agent._q_network)
    cloned_q_net.build(agent.action_spec)
    dummy_datapoint = tf.random.uniform((1,) + env.time_step_spec().observation.shape)
    cloned_q_net(dummy_datapoint)
    cloned_q_net.set_weights((agent._q_network.get_weights()))
    return cloned_q_net


class MessagePrinter:
    def __init__(self, interval):
        self.interval = interval
        self.last_print_time = time.time()

    def print_message(self, message):
        current_time = time.time()
        if current_time - self.last_print_time >= self.interval:
            now = datetime.now()
            current_time_str = now.strftime("%H:%M")  # Formatieren der Zeit als Stunden:Minuten
            print(f"{current_time_str} - {message}")
            self.last_print_time = current_time
