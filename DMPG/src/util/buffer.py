import tensorflow as tf
from tf_agents.replay_buffers import py_uniform_replay_buffer
import numpy as np
from setproctitle import setproctitle


def process_worker_buffer(q_worker_buffer):
    # Get data from the worker buffer
    work_buffer_data = q_worker_buffer.get()
    # Stack the work buffer data using TensorFlow nest map function
    stacked_work_data = tf.nest.map_structure(lambda t: tf.stack([t] * 1), work_buffer_data)
    return stacked_work_data


def buffer_process(q_worker_buffer, q_buffer_agent, buffer_spec, process_active, q_rewards,
                   print_interval=500):
    setproctitle('buffer-process')
    try:
        # Initialize replay buffer with large capacity and buffer spec
        replay_buffer = py_uniform_replay_buffer.PyUniformReplayBuffer(
            capacity=10 ** 6,
            data_spec=buffer_spec)
        # Counter to track reward intervals
        # Iterate initial 100 times and populate replay buffer
        for i in range(500):
            # Get the stacked work data and add it to the replay buffer
            stacked_work_data = process_worker_buffer(q_worker_buffer)
            replay_buffer.add_batch(stacked_work_data)
        # Infinite loop to continuously monitor and process buffer
        while True:
            # If worker buffer is not empty, get data and add it to replay buffer
            if not q_worker_buffer.empty():
                stacked_work_data = process_worker_buffer(q_worker_buffer)
                replay_buffer.add_batch(stacked_work_data)
                reward = np.sum(stacked_work_data.reward)
                q_rewards.put(reward)
            # If the agent buffer is not full, get the next sample and add it to the buffer
            train_batch = replay_buffer.get_next(sample_batch_size=32, num_steps=2)
            try:
                q_buffer_agent.put(train_batch)
            except Exception as e:
                print(f"Error adding train batch to queue: {e}")
            tf.keras.backend.clear_session()
    except Exception as e:
        print(f"An error occurred: {e}")
