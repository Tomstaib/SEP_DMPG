import datetime
import time
import tensorflow as tf
import multiprocessing as mp
import numpy as np
import src.util.scheduling as scheduling
import matplotlib.pyplot as plt
import pandas as pd
import psutil
import GPUtil

from tf_agents.specs import tensor_spec
from util.dqn import create_agent, clone_network, train_process
from util.buffer import buffer_process
from models.test_DQN import setup_model_pcb
from src.util.simulations import run_rl_train_simulation
from setproctitle import setproctitle


# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        tf.config.experimental.set_memory_growth(gpus[0], True)
    except RuntimeError as e:
        print(e)


def worker_process(q_net, q_worker_buffer, q_new_network, q_utilization, epsilon, params):
    setproctitle('worker-process')
    network = q_net
    while True:
        processing_time = run_rl_train_simulation(model=setup_model_pcb, minutes=501, params=params, q_net=network, epsilon=epsilon.value, queue=q_worker_buffer)
        utilization = processing_time * 100 / 500
        q_utilization.put(utilization)
        if not q_new_network.empty():
            network = q_new_network.get()
        tf.keras.backend.clear_session()


def analyse_process(process, iteration, output=False):
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        if process['name'] in proc.info['name']:
            cpu = proc.info['cpu_percent']
            ram = proc.info['memory_info'].rss / (1024 * 1024)
            process['cpu'] = (process['cpu'] * (iteration - 1) + cpu) / iteration
            process['ram'] = (process['ram'] * (iteration - 1) + ram) / iteration
            if output:
                print(process['name'], ': current cpu: ', cpu, '%, average cpu: ', process['cpu'], '%, current ram: ',
                      ram, 'MB, average ram: ', process['ram'], 'MB')
            return process


def observer_process(q_losses, q_rewards, q_utilization, epsilon, print_intervals=100, time_between_prints=(1), analyze_process=False):
    setproctitle('observer-process')
    losses = CompressedData(100000)
    rewards = CompressedData(100000)
    utilization = CompressedData(100000)
    if analyze_process:
        gpu_load = 0
        gpu_memory = 0
        worker_process_data = {'name': 'worker-process', 'cpu': 0, 'ram': 0}
        observer_process_data = {'name': 'observer-process', 'cpu': 0, 'ram': 0}
        train_process_data = {'name': 'train-process', 'cpu': 0, 'ram': 0}
        buffer_process_data = {'name': 'buffer-process', 'cpu': 0, 'ram': 0}
    i = 0
    start_time = datetime.datetime.now()
    while True:
        i += 1
        if i % 60 == 0:
            output = True
        else:
            output = False
        time.sleep(time_between_prints)
        if analyze_process:

            worker_process_data = analyse_process(worker_process_data, i, output)
            observer_process_data = analyse_process(observer_process_data, i, output)
            train_process_data = analyse_process(train_process_data, i, output)
            buffer_process_data = analyse_process(buffer_process_data, i, output)
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                print(f"GPU ID: {gpu.id}, Auslastung: {gpu.load * 100}%, Speicher: {gpu.memoryUsed} MB / {gpu.memoryTotal} MB")
                load = gpu.load * 100
                memory = gpu.memoryUsed
                gpu_load = (gpu_load * (i - 1) + load) / i
                gpu_memory = (gpu_memory * (i - 1) + memory) / i
                if output:
                    print('GPU: current load:', load, '%, average load: ', gpu_load, '%, current memory: ',
                          memory, 'MB, average memory: ', gpu_memory, 'MB')
                    print('Current processing time: ', datetime.datetime.now() - start_time)
                    print(f'Current epsilon {epsilon.value:.2f}')
                    print('___________________________________________________________________________')
        if i % (1 * 60) == 0:

            losses = plot_average_interval(q_losses, losses, 'Loss', print_intervals)
            rewards = plot_average_interval(q_rewards, rewards, 'reward', print_intervals)
            utilization = plot_average_interval(q_utilization, utilization, 'Utilization', print_intervals, percentile=True)


def plot_average_interval(queue, data, label, print_intervals, minmax=False, percentile=False):
    data = process_data(data, queue)
    # Creating equal length intervals
    if print_intervals > len(data.data):
        print_intervals = len(data.data)
    intervals = np.array_split(data.data, print_intervals)

    # Computing the averages, minimum, maximum and percentiles for each interval
    averages = [np.mean(interval) for interval in intervals]
    if minmax:
        minimums = [np.min(interval) for interval in intervals]
        maximums = [np.max(interval) for interval in intervals]
    if percentile:
        percentiles_5 = [np.percentile(interval, 5) for interval in intervals]
        percentiles_95 = [np.percentile(interval, 95) for interval in intervals]

    # Update the font size for all elements in the plot
    plt.rcParams.update({'font.size': 12})

    # Generating a graph for the temporal progression of the average, min, max, and percentiles
    x_range = range(len(averages))

    # Plot averages with red color
    plt.plot(x_range, averages, color='green', label='Average')

    if minmax:
        # Plot minimums with blue color
        plt.plot(x_range, minimums, color='cyan', label='Min')
        # Plot maximums with green color
        plt.plot(x_range, maximums, color='magenta', label='Max')

    if percentile:
        # Plot 5% percentile with cyan color
        plt.plot(x_range, percentiles_5, color='blue', label='5% Percentile')
        # Plot 95% percentile with magenta color
        plt.plot(x_range, percentiles_95, color='red', label='95% Percentile')

    plt.title(f'Time Series of {label.capitalize()} in {print_intervals} Intervals')
    plt.xlabel(f'Number of Individual Values in an Interval: {data.original_count // print_intervals}')
    plt.ylabel(f'{label.capitalize()} Value')

    # Add a legend
    plt.legend(loc='best')
    plt.grid(True)
    # plt.savefig(label.capitalize() + ".jpg", dpi=300, figsize=(3.2, 2.4))
    plt.show(dpi=400, figsize=(3.2, 2.4))

    # Print the average of the last interval to the console
    print(f'Durchschnittlicher {label} der letzten {data.original_count // print_intervals}: {averages[-1]}')

    # Daten in pandas DataFrame speichern
    df = pd.DataFrame(data.data, columns=[label])

    if minmax:
        df['Min'] = minimums
        df['Max'] = maximums
    # if percentile:
        # df['5th percentile'] = percentiles_5
        # df['95th percentile'] = percentiles_95

    # DataFrame als CSV-Datei speichern
    df.to_csv('data.csv', index=False)

    return data


class CompressedData:
    def __init__(self, max_size: int):
        self.data = np.array([])
        self.compression_factor = 1
        self.max_size = max_size
        self.original_count = 0


def process_data(comp_data: CompressedData, queue: mp.Queue):
    # Process and compress new data from queue
    while not queue.empty():
        new_values = np.array([queue.get() for _ in range(comp_data.compression_factor)])
        new_value = np.mean(new_values)
        comp_data.original_count += len(new_values)
        comp_data.data = np.append(comp_data.data, new_value)

    # Check if length of the array exceeds max_size
    if len(comp_data.data) > comp_data.max_size:
        # Double the compression factor
        comp_data.compression_factor *= 2
        # Regroup the data and calculate the averages
        reshaped_data = comp_data.data[:len(comp_data.data) // comp_data.compression_factor * comp_data.compression_factor].reshape(-1, comp_data.compression_factor)
        comp_data.data = np.mean(reshaped_data, axis=1)
        # If there are still values remaining that do not fit into the new grouping
        remaining_values = comp_data.data[len(comp_data.data) // comp_data.compression_factor * comp_data.compression_factor:]
        if len(remaining_values) > 0:
            comp_data.data = np.append(comp_data.data, np.mean(remaining_values))

    return comp_data


if __name__ == '__main__':

    learning_rate_function = tf.keras.optimizers.schedules.PolynomialDecay(
        initial_learning_rate=10e-4,
        end_learning_rate=10e-6,
        decay_steps=(4000 * 100)
    )

    params = [
        2,                          # num actions
        (16, 34),                   # fc_layer_params
        learning_rate_function,     # learning_rate
        scheduling.SchedulingEnv()  # env
    ]

    tf.random.set_seed(3)

    num_worker_processes = 1
    env = scheduling.SchedulingEnv()
    central_agent = create_agent(params, 0.1)
    buffer_spec = tensor_spec.to_array_spec(central_agent.collect_data_spec)

    q_worker_buffer = mp.get_context("spawn").Queue(maxsize=1000)
    q_buffer_agent = mp.get_context("spawn").Queue(maxsize=10)
    q_new_network = mp.get_context("spawn").Queue(maxsize=2)
    q_losses = mp.get_context("spawn").Queue()
    q_rewards = mp.get_context("spawn").Queue()
    q_utilization = mp.get_context("spawn").Queue()

    process_active = mp.get_context("spawn").Value('b', True)
    epsilon = mp.get_context("spawn").Value('d', 1)

    processes = []
    for worker in range(num_worker_processes):
        cloned_q_net = clone_network(central_agent, params)
        processes.append(mp.get_context("spawn").Process(target=worker_process, name='worker-process',
                                                         args=(cloned_q_net, q_worker_buffer, q_new_network,
                                                               q_utilization, epsilon, params)))
    processes.append(mp.get_context("spawn").Process(target=buffer_process,
                                                     args=(q_worker_buffer, q_buffer_agent, buffer_spec,
                                                           process_active, q_rewards)))
    cloned_q_net = clone_network(central_agent, params)
    processes.append(mp.get_context("spawn").Process(target=train_process, name='train-process',
                                                     args=(cloned_q_net, q_buffer_agent, q_new_network,
                                                           epsilon, q_losses, params)))
    processes.append(mp.get_context("spawn").Process(target=observer_process, name='observer-process',
                                                     args=(q_losses, q_rewards, q_utilization, epsilon)))

    for process in processes:
        process.start()

    for process in processes:
        process.join()
