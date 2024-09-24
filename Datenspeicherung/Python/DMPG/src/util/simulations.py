import random
import time
from datetime import timedelta, datetime
from typing import Callable, Union

import simpy
import pandas as pd
import numpy as np
import concurrent.futures
import logging
import database_connection

from orm import PivotTable, Simulation, Scenario, Model, HSUser
from src.core.entity import EntityManager
from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
from src.util.global_imports import Stats, RANDOM_SEED
from src.util.helper import round_value

global seconds_previous_computations


def run_simulation(model: Callable, minutes: Union[int, float], store_pivot_in_file: str = None):
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

    # Create Pivot Table
    pivot_table = df.pivot_table(index=['Type', 'Name', 'Stat'], values='Value', aggfunc='mean')

    # Print Pivot Table
    logging.info(pivot_table)

    # Optionally save to CSV
    if store_pivot_in_file:
        pivot_table.to_csv(store_pivot_in_file)

    return pivot_table


def calculate_statistics(env):
    # Calculate entity statistics
    all_entities = EntityManager.entities

    times_in_system = [entity.destruction_time - entity.creation_time
                       for entity in all_entities if entity.destruction_time]

    logging.debug(f"Entities not processed: {len(all_entities)} - {len(times_in_system)} "
                  f"= {len(all_entities) - len(times_in_system)} "
                  f"({len(times_in_system) / len(all_entities)} %)")

    if times_in_system:
        avg_time_in_system = sum(times_in_system) / len(times_in_system)
        max_time_in_system = max(times_in_system)
        min_time_in_system = min(times_in_system)
    else:
        avg_time_in_system = max_time_in_system = min_time_in_system = 0

    number_created = len(all_entities)
    number_destroyed = sum(entity.destruction_time is not None for entity in all_entities)

    entity_stats = {
        'NumberInSystem': len(all_entities),
        'AvgTimeInSystem': avg_time_in_system,
        'MaxTimeInSystem': max_time_in_system,
        'MinTimeInSystem': min_time_in_system,
        'NumberCreated': number_created,
        'NumberDestroyed': number_destroyed
    }

    # Calculate server statistics
    server_stats = []
    for server in Server.servers:
        current_simulation_time = env.now
        scheduled_utilization = (server.units_utilized / current_simulation_time) * 100 \
            if current_simulation_time > 0 else 0
        avg_time_processing = (server.total_processing_time / server.entities_processed
                               if server.entities_processed > 0 else 0)

        server_stats.append({
            'Server': server.name,
            'ScheduledUtilization': scheduled_utilization,
            'UnitsUtilized': server.units_utilized,
            'AvgTimeProcessing': avg_time_processing,
            'TotalTimeProcessing': server.total_processing_time,
            'NumberEntered': server.number_entered,
            'NumberExited': server.number_exited,
            'NumberDowntimes': server.number_downtimes,
            'TotalDowntime': server.total_downtime
        })

    # Calculate sink statistics
    sink_stats = {}
    for sink in Sink.all_sinks:
        avg_time_in_system = (sink.total_time_in_system / sink.entities_processed
                              if sink.entities_processed > 0 else 0)
        sink_stats[sink.name] = {
            'AvgTimeInSystem': avg_time_in_system,
            'MaxTimeInSystem': sink.max_time_in_system,
            'MinTimeInSystem': sink.min_time_in_system if sink.entities_processed > 0 else None,
            'NumberEntered': sink.number_entered,
        }

    # Calculate source statistics
    source_stats = {}
    for source in Source.sources:
        source_stats[source.name] = {
            'NumberCreated': source.entities_created,
            'NumberExited': source.number_exited,
        }

    return entity_stats, server_stats, sink_stats, source_stats


def replication(env_setup_func, calculate_stats_func, minutes, r):
    random.seed(r)
    EntityManager.destroy_all_entities()
    Source.reset_all()
    Server.reset_all()
    Sink.reset_all()
    env = simpy.Environment()
    env_setup_func(env)
    env.run(until=minutes)
    return calculate_stats_func(env)


def get_percentage_and_computingtimes(computing_time_start, i, num_replications):
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


def run_replications(model_name, scenario_name, user_name, model: Callable, minutes, num_replications,
                     multiprocessing=False,
                     save_pivot_to_database: bool = False):
    global seconds_previous_computations
    seconds_previous_computations = 0
    start = time.time()
    local_start_time = datetime.now()  # For database

    engine = database_connection.connect_to_db()

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

    Stats.all_detailed_stats = []

    def process_results(entity_stats, server_stats, sink_stats, source_stats):
        all_entity_stats.append(entity_stats)
        for server_stat in server_stats:
            server_name = server_stat['Server']
            all_server_stats.setdefault(server_name, []).append(server_stat)
        for sink_name, stat in sink_stats.items():
            all_sink_stats.setdefault(sink_name, []).append(stat)
        for source_name, stat in source_stats.items():
            all_source_stats.setdefault(source_name, []).append(stat)

        detailed_stats = {
            'Entity': entity_stats,
            'Server': server_stats,
            'Sink': sink_stats,
            'Source': source_stats
        }
        Stats.all_detailed_stats.append(detailed_stats)

    tenth_percentage = int(num_replications / 10)

    if multiprocessing:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_results = [executor.submit(replication, model, calculate_statistics, minutes, r)
                              for r in range(num_replications)]
            for r, future in enumerate(concurrent.futures.as_completed(future_results)):
                process_results(*future.result())
                print_stats(r, num_replications, start, tenth_percentage)
    else:
        for r in range(num_replications):
            process_results(*replication(model, calculate_statistics, minutes, r))
            print_stats(r, num_replications, start, tenth_percentage)

    local_end_time = datetime.now()  # For database

    if save_pivot_to_database:
        combined_pivot = create_pivot(all_entity_stats, all_server_stats, all_sink_stats, all_source_stats,
                                      entity_stat_names,
                                      server_stat_names, sink_stat_names, source_stat_names, engine)
        save_to_database(combined_pivot, engine, local_start_time, local_end_time, model_name, scenario_name, minutes,
                         num_replications, user_name)

    return create_pivot(all_entity_stats, all_server_stats, all_sink_stats, all_source_stats, entity_stat_names,
                        server_stat_names, sink_stat_names, source_stat_names, engine)


def print_stats(i, num_replications, start, tenth_percentage):
    if tenth_percentage == 0 or (i + 1) % tenth_percentage == 0:
        ct = get_percentage_and_computingtimes(start, i, num_replications)
        logging.info(f"{ct[0]} replication {i + 1}/{num_replications}\t{ct[1]}\t{ct[2]}\t{ct[3]}\t{ct[4]}")


def create_pivot(all_entity_stats, all_server_stats, all_sink_stats, all_source_stats, entity_stat_names,
                 server_stat_names, sink_stat_names, source_stat_names, engine, store_pivot_in_file: str = None):
    def calculate_aggregate_stats(values):
        numeric_values = [value for value in values if isinstance(value, (int, float))]
        if not numeric_values:
            return None, None, None, None

        avg = np.mean(numeric_values)
        min_val = np.min(numeric_values)
        max_val = np.max(numeric_values)
        half_width = 1.96 * (np.std(numeric_values) / np.sqrt(len(numeric_values)))
        return avg, min_val, max_val, half_width

    def flatten_stats(stats, name, stat_names, is_entity=False):
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
    # Creating the pivot table
    pivot_table_combined = df_combined.pivot_table(
        index=['Type', 'Name', 'Stat'],
        values=['Average', 'Minimum', 'Maximum', 'Half-Width'],
        aggfunc='mean'
    )
    # Reorder the columns
    pivot_table_combined = pivot_table_combined[['Average', 'Minimum', 'Maximum', 'Half-Width']]
    # Print the Pivot Table
    logging.info(pivot_table_combined)

    if store_pivot_in_file:
        pivot_table_combined.to_csv('combined_simulation_stats.csv')

    return pivot_table_combined


def save_to_database(combined_pivot, engine, local_start_time, local_end_time, model_name, scenario_name, minutes,
                     num_replications, user_name):
    session = database_connection.create_session(engine)
    try:
        # Check if user exist, if not create
        user_id = database_connection.get_or_create_user(session, user_name)

        pivot_table_id = database_connection.get_next_pivot_table_id(session)

        # Create Model
        new_model = Model(model_name=model_name, user_id=user_id)
        session.add(new_model)
        session.flush()

        # Create Scenario
        new_scenario = Scenario(scenario_name=scenario_name, minutes=minutes, model_id=new_model.model_id)
        session.add(new_scenario)
        session.flush()

        # Create Simulation
        new_simulation = Simulation(local_start_time=local_start_time, local_end_time=local_end_time,
                                    num_replications=num_replications, scenario_id=new_scenario.scenario_id)
        session.add(new_simulation)
        session.flush()

        # PivotTable entries added to the session
        pivot_entries = []
        for index, row in combined_pivot.iterrows():
            pivot_entry = PivotTable(
                pivot_table_id=pivot_table_id,
                simulation_id=new_simulation.simulation_id,  # 'SimulationsID'
                type=index[0],  # 'Type'
                name=index[1],  # 'Name'
                stat=index[2],  # 'Stat'
                average=row['Average'],  # 'Average'
                minimum=row['Minimum'],  # 'Minimum'
                maximum=row['Maximum'],  # 'Maximum'
                half_width=row['Half-Width']  # 'Half-Width'
            )
            pivot_entries.append(pivot_entry)
            pivot_table_id += 1  # Increment after each row

        # All PivotTable entries added
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()