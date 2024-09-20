import gc
import os
import random
import time
from datetime import timedelta
from typing import Callable, Union, Tuple
import simpy
import pandas as pd
import numpy as np
import concurrent.futures
import logging


import src.util.global_imports as gi

from src.core.entity import EntityManager
from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
from src.util.global_imports import RANDOM_SEED, Stats, set_duration_warm_up
from src.util.helper import round_value

global seconds_previous_computations


def run_simulation(model: Callable, minutes: Union[int, float], warm_up: Union[int, float] = None,
                   store_pivot_in_file: str = None) -> pd.DataFrame:
    """
    Run a simulation using the specified model for the given number of minutes.

    :param model (Callable): The simulation model function.
    :param minutes (int): The number of minutes to run the simulation.

    :return pivot_table (DataFrame): The pivot
    """

    if warm_up is not None:
        set_duration_warm_up(warm_up)

    print(gi.DURATION_WARM_UP)

    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    model(env)
    env.run(until=minutes)

    # Get the statistics
    entity_stats, server_stats, sink_stats, source_stats = calculate_statistics(env)

    # Structure the data for the DataFrame
    data = []

    # Function to round the values

    # Entity Stats
    for key, value in entity_stats.items():
        data.append({'Type': 'Entity', 'Name': 'Entity', 'Stat': key, 'Value': round_value(value)})

    # Server Stats
    for stat in server_stats:
        for key, value in stat.items():
            if key != 'Server':
                data.append({'Type': 'Server', 'Name': stat['Server'], 'Stat': key, 'Value': round_value(value)})

    # Sink Stats
    for sink_name, stats in sink_stats.items():
        for key, value in stats.items():
            data.append({'Type': 'Sink', 'Name': sink_name, 'Stat': key, 'Value': round_value(value)})

    # Source Stats
    for source_name, stats in source_stats.items():
        for key, value in stats.items():
            data.append({'Type': 'Source', 'Name': source_name, 'Stat': key, 'Value': round_value(value)})

    # Create DataFrame
    df = pd.DataFrame(data)

    # Optimize DataFrame memory usage
    df['Value'] = pd.to_numeric(df['Value'], downcast='float')  # Downcast to float32 if possible
    df['Type'] = df['Type'].astype('category')  # Convert to categorical type
    df['Name'] = df['Name'].astype('category')  # Convert to categorical type
    df['Stat'] = df['Stat'].astype('category')  # Convert to categorical type

    # Create Pivot Table
    pivot_table = df.pivot_table(index=['Type', 'Name', 'Stat'], values='Value', aggfunc='mean')

    # Print Pivot Table
    logging.info(pivot_table)

    # Optionally save to CSV
    if store_pivot_in_file:
        pivot_table.to_csv(store_pivot_in_file)

    return pivot_table


def calculate_statistics(env) -> Tuple:
    """
    Calculate various statistics based on the simulation environment.

    :param env: The simulation environment.

    :return Tuple[Dict, List[Dict], Dict, Dict]: A tuple containing dictionaries for entity, server, sink,
     and source statistics.
    """
    # Calculate entity statistics
    all_entities_with_warm_up_time = EntityManager.entities
    all_entities = []

    for objekt in all_entities_with_warm_up_time:
        if objekt.destruction_time is not None:
            if objekt.destruction_time > gi.DURATION_WARM_UP:
                all_entities.append(objekt)
            else:
                pass
        else:
            all_entities.append(objekt)

    times_in_system = [entity.destruction_time - entity.creation_time
                       for entity in all_entities if entity.destruction_time]

    logging.debug(f"Entities not processed: {len(all_entities)} - {len(times_in_system)} "
                  f"= {len(all_entities) - len(times_in_system)} "
                  f"({len(times_in_system) / len(all_entities)} %)")

    if times_in_system:
        avg_time_in_system_pivot_table = sum(times_in_system) / len(times_in_system)
        max_time_in_system_pivot_table = max(times_in_system)
        min_time_in_system_pivot_table = min(times_in_system)
    else:
        avg_time_in_system_pivot_table = max_time_in_system_pivot_table = min_time_in_system_pivot_table = 0

    number_created_pivot_table = len(all_entities)
    number_destroyed_pivot_table = sum(entity.destruction_time is not None for entity in all_entities)

    entity_stats = {
        'NumberInSystem': len(all_entities),
        'AvgTimeInSystem': avg_time_in_system_pivot_table,
        'MaxTimeInSystem': max_time_in_system_pivot_table,
        'MinTimeInSystem': min_time_in_system_pivot_table,
        'NumberCreated': number_created_pivot_table,
        'NumberDestroyed': number_destroyed_pivot_table
    }
    # Calculate server statistics
    server_stats = []
    for server in Server.servers:
        current_simulation_time = env.now
        scheduled_utilization_pivot_table = 0
        avg_time_processing_pivot_table = 0
        if env.now > gi.DURATION_WARM_UP:
            scheduled_utilization_pivot_table = (server.units_utilized_pivot_table / current_simulation_time) * 100 \
                if current_simulation_time > 0 else 0
            avg_time_processing_pivot_table = (
                server.total_processing_time_pivot_table / server.entities_processed
                if server.entities_processed > 0 else 0)

        server_stats.append({
            'Server': server.name,
            'ScheduledUtilization': scheduled_utilization_pivot_table,
            'UnitsUtilized': server.units_utilized_pivot_table,
            'AvgTimeProcessing': avg_time_processing_pivot_table,
            'TotalTimeProcessing': server.total_processing_time_pivot_table,
            'NumberEntered': server.number_entered_pivot_table,
            'NumberExited': server.number_exited_pivot_table,
            'NumberDowntimes': server.number_downtimes_pivot_table,
            'TotalDowntime': server.total_downtime_pivot_table
        })

    # Calculate sink statistics
    sink_stats = {}
    for sink in Sink.sinks:

        if sink.tally_statistic.num_times_processed_list:
            tally_min, tally_max, tally_avg = sink.tally_statistic.calculate_statistics()
        else:
            tally_min, tally_max, tally_avg = None, None, None

        avg_time_in_system_pivot_table = (
            sink.total_time_in_system / sink.entities_processed
            if sink.entities_processed > 0 else 0)

        sink_stats[sink.name] = {
            'AvgTimeInSystem': avg_time_in_system_pivot_table,
            'MaxTimeInSystem': sink.max_time_in_system_pivot_table,
            'MinTimeInSystem': sink.min_time_in_system_pivot_table if sink.entities_processed > 0 else None,
            'NumberEntered': sink.number_entered_pivot_table,

            'NumTimesProcessed_Avg': tally_avg,
            'NumTimesProcessed_Max': tally_max,
            'NumTimesProcessed_Min': tally_min,
        }

    # Calculate source statistics
    source_stats = {}
    for source in Source.sources:
        source_stats[source.name] = {
            'NumberCreated': source.entities_created_pivot_table,
            'NumberExited': source.number_exited_pivot_table,
        }

    return entity_stats, server_stats, sink_stats, source_stats


def replication(env_setup_func, calculate_stats_func, minutes, r) -> pd.DataFrame:
    """
    Replicate a simulation run.

    :param env_setup_func (Callable): A function that sets up the simulation environment.
    :param calculate_stats_func (Callable): A function that calculates statistics based on the simulation environment.
    :param minutes (int): The number of minutes to run the replication.
    :param r (int): iteration.

    :return Tuple[Dict, List[Dict], Dict, Dict]: A tuple containing dictionaries for entity, server, sink, and source statistics.
    """
    random.seed(r)
    EntityManager.destroy_all_entities()
    Source.sources.reset_all()
    Server.servers.reset_all()
    Sink.sinks.reset_all()
    env = simpy.Environment()
    env_setup_func(env)
    env.run(until=minutes)

    result = calculate_stats_func(env)

    del env
    gc.collect()
    return result


def get_percentage_and_computingtimes(computing_time_start, i, num_replications) -> Tuple[str, str, str, str, str]:
    """
    Calculate the percentage completion and various time metrics for a set of replications.

    param: computing_time_start (float): The start time of the computation.
    param: i (int): The current iteration number.
    param: num_replications (int): The total number of replications.

    return: Tuple[Dict, List[Dict], Dict, Dict]: A tuple containing formatted strings for percentage completion and time metrics.
    """
    global seconds_previous_computations

    seconds_computed = time.time() - computing_time_start
    seconds_computed_iteration = seconds_computed - seconds_previous_computations
    seconds_previous_computations = seconds_computed

    percentage = round((i + 1) / num_replications * 100)
    total_seconds_to_complete = seconds_computed / (percentage / 100)

    return (f"{percentage:>3}%",
            f"[time computed] {str(timedelta(seconds=seconds_computed)):<15}",
            f"[time to complete] {str(timedelta(seconds=total_seconds_to_complete - seconds_computed)):<15}",
            f"[time prediction] {str(timedelta(seconds=total_seconds_to_complete)):<15}",
            f"[time per iteration] {str(timedelta(seconds=seconds_computed_iteration)):<15}")


def run_replications(model: Callable, minutes, num_replications, warm_up: Union[int, float] = None,
                     multiprocessing=False) -> tuple:
    """
    Run multiple replications of a simulation and collect statistics.

    param: model (Callable): The simulation model function.
    param: minutes (int): The number of minutes to run each replication.
    param: num_replications (int): The total number of replications.
    param: multiprocessing (bool): Whether to use multiprocessing for parallel execution.
    """

    if warm_up is not None:
        set_duration_warm_up(warm_up)

    global seconds_previous_computations
    seconds_previous_computations = 0
    start = time.time()

    # Define the names of the statistics for entities, servers, sinks, and sources
    entity_stat_names = ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem',
                         'NumberCreated', 'NumberDestroyed', 'NumberInSystem']
    server_stat_names = ['ScheduledUtilization', 'UnitsUtilized', 'AvgTimeProcessing',
                         'TotalTimeProcessing', 'NumberEntered', 'NumberExited', 'TotalDowntime', 'NumberDowntimes']
    sink_stat_names = ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem', 'NumberEntered']
    source_stat_names = ['NumberCreated', 'NumberExited']

    all_entity_stats = []
    all_server_stats = {}
    all_sink_stats = {}
    all_source_stats = {}

    # Stats.all_detailed_stats = []

    def process_results(entity_stats, server_stats, sink_stats, source_stats) -> None:
        """
        Process the results of a single replication and store the statistics.

        param: entity_stats (Dict): Statistics for entities.
        param: server_stats (List[Dict]): Statistics for servers.
        param: sink_stats (Dict): Statistics for sinks.
        param: source_stats (Dict): Statistics for sources.
        """
        all_entity_stats.append(entity_stats)
        for server_stat in server_stats:
            server_name = server_stat['Server']
            all_server_stats.setdefault(server_name, []).append(server_stat)
        for sink_name, stat in sink_stats.items():
            all_sink_stats.setdefault(sink_name, []).append(stat)
        for source_name, stat in source_stats.items():
            all_source_stats.setdefault(source_name, []).append(stat)

        """detailed_stats = {
            'Entity': entity_stats,
            'Server': server_stats,
            'Sink': sink_stats,
            'Source': source_stats
        }
        Stats.all_detailed_stats.append(detailed_stats)"""
        """Stats.all_detailed_stats.append({
            'Entity': entity_stats,
            'Server': server_stats,
            'Sink': sink_stats,
            'Source': source_stats
        })"""

    tenth_percentage = int(num_replications / 10)

    """if multiprocessing:
        chunk_size = max(1, num_replications // (os.cpu_count() or 1))
        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = executor.map(
                replication,
                [model] * num_replications,
                [calculate_statistics] * num_replications,
                [minutes] * num_replications,
                range(num_replications),
                chunksize=chunk_size
            )
            for r, result in enumerate(results, 1):
                process_results(*result)
                if r % tenth_percentage == 0 or r == num_replications:
                    print_stats(r, num_replications, start, tenth_percentage)
    else:
        for r in range(num_replications):
            process_results(*replication(model, calculate_statistics, minutes, r))
            if r % tenth_percentage == 0 or r == num_replications:
                print_stats(r, num_replications, start, tenth_percentage)"""

    if multiprocessing:
        num_cores = min(os.cpu_count(), num_replications)
        print(f"Running on {num_cores} cores")
        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
                future_results = [executor.submit(replication, model, calculate_statistics, minutes, r)
                                  for r in range(num_replications)]
                for r, future in enumerate(concurrent.futures.as_completed(future_results)):
                    process_results(*future.result())
                    print_stats(r, num_replications, start, tenth_percentage)
        except Exception as e:
            print(f"An Exception occurred: {e}")
    else:
        for r in range(num_replications):
            process_results(*replication(model, calculate_statistics, minutes, r))
            print_stats(r, num_replications, start, tenth_percentage)

    # print(Stats.all_detailed_stats)

    return create_pivot(all_entity_stats, all_server_stats, all_sink_stats, all_source_stats, entity_stat_names,
                        server_stat_names, sink_stat_names, source_stat_names)


def print_stats(i, num_replications, start, tenth_percentage) -> None:
    """
    Prints statistics
    :param i: index
    :param num_replications:
    :param start:
    :param tenth_percentage:
    :return:
    """
    if tenth_percentage == 0 or (i + 1) % tenth_percentage == 0:
        ct = get_percentage_and_computingtimes(start, i, num_replications)
        logging.info(f"{ct[0]} replication {i + 1}/{num_replications}\t{ct[1]}\t{ct[2]}\t{ct[3]}\t{ct[4]}")


def create_pivot(all_entity_stats, all_server_stats, all_sink_stats, all_source_stats, entity_stat_names,
                 server_stat_names, sink_stat_names, source_stat_names, store_pivot_in_file: str = None) -> tuple:
    """
        Create a pivot table from collected simulation statistics.

        param: all_entity_stats (list): List of entity statistics from multiple replications.
        param: all_server_stats (dict): Dictionary of server statistics from multiple replications.
        param: all_sink_stats (dict): Dictionary of sink statistics from multiple replications.
        param: all_source_stats (dict): Dictionary of source statistics from multiple replications.
        param: entity_stat_names (list): List of entity statistics names.
        param: server_stat_names (list): List of server statistics names.
        param: sink_stat_names (list): List of sink statistics names.
        param: source_stat_names (list): List of source statistics names.
        """

    def calculate_aggregate_stats(values) -> tuple:
        """
        Calculate aggregate statistics (average, minimum, maximum, half-width).

        param: values (list): List of numeric values.

        return: Tuple: Tuple containing average, minimum, maximum, half
        """
        numeric_values = [value for value in values if isinstance(value, (int, float))]
        if not numeric_values:
            return None, None, None, None

        avg = np.mean(numeric_values)
        min_val = np.min(numeric_values)
        max_val = np.max(numeric_values)
        half_width = 1.96 * (np.std(numeric_values) / np.sqrt(len(numeric_values)))
        return avg, min_val, max_val, half_width

    def flatten_stats(stats, name, stat_names, is_entity=False) -> list:
        """
        Flatten statistics into a list for DataFrame.

        param: stats (dict): Dictionary containing statistics for a particular component.
        param: name (str): Name of the component type (Entity, Server, Sink, Source).
        param: stat_names (list): List of statistic names.
        param: is_entity (bool): Indicates if the component is an entity.

        return: List of dictionaries containing statistics for a particular component
        """
        flattened = []
        for component_name, stat_values in stats.items():
            for stat_name in stat_names:
                values = stat_values.get(stat_name, {}) if is_entity else stat_values.get(stat_name)
                if values:
                    avg, min_val, max_val, half_width = values if is_entity else \
                        (values[0], values[1], values[2], values[3])
                    row = {'Type': name, 'Name': component_name, 'Stat': stat_name,
                           'Average': round(avg, 4) if avg is not None else None,
                           'Minimum': round(min_val, 4) if min_val is not None else None,
                           'Maximum': round(max_val, 4) if max_val is not None else None,
                           'Half-Width': round(half_width, 4) if half_width is not None else None}
                    flattened.append(row)
        return flattened

    # Calculate aggregate statistics
    entity_aggregate_stats = {stat: calculate_aggregate_stats([run[stat] for run in all_entity_stats])
                              for stat in entity_stat_names}
    modified_entity_stats = {'Entity': {}}
    for stat_name, values in entity_aggregate_stats.items():
        avg, min_val, max_val, half_width = values if values else (None, None, None, None)
        modified_entity_stats['Entity'][stat_name] = (avg, min_val, max_val, half_width)
    aggregate_server_stats = {server_name: {key: calculate_aggregate_stats([stat[key] for stat in stats_list])
                                            for key in server_stat_names}
                              for server_name, stats_list in all_server_stats.items()}
    aggregate_sink_stats = {sink_name: {key: calculate_aggregate_stats([stat[key] for stat in stats_list])
                                        for key in sink_stat_names}
                            for sink_name, stats_list in all_sink_stats.items()}
    aggregate_source_stats = {source_name: {key: calculate_aggregate_stats([stat[key] for stat in stats_list])
                                            for key in source_stat_names}
                              for source_name, stats_list in all_source_stats.items()}

    # Flatten all stats into a single list
    flattened_stats = []
    flattened_stats.extend(flatten_stats(modified_entity_stats, 'Entity', entity_stat_names, is_entity=True))
    flattened_stats.extend(flatten_stats(aggregate_server_stats, 'Server', server_stat_names))
    flattened_stats.extend(flatten_stats(aggregate_sink_stats, 'Sink', sink_stat_names))
    flattened_stats.extend(flatten_stats(aggregate_source_stats, 'Source', source_stat_names))
    # Creating a combined DataFrame from flattened stats
    df_combined = pd.DataFrame(flattened_stats)

    pivot_table_combined = df_combined.pivot_table(
        index=['Type', 'Name', 'Stat'],
        values=['Average', 'Minimum', 'Maximum', 'Half-Width'],
        aggfunc='mean'
    )
    # Reorder the columns
    pivot_table_combined = pivot_table_combined[['Average', 'Minimum', 'Maximum', 'Half-Width']]
    # Print the Pivot Table
    logging.info("\n" + str(pivot_table_combined))

    if store_pivot_in_file:
        pivot_table_combined.to_csv('combined_simulation_stats.csv')

    return pivot_table_combined
