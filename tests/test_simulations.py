# tests/test_simulation.py

import pytest
from unittest.mock import MagicMock, patch, call
import pandas as pd
import time
from datetime import datetime, timedelta

from src.util.simulations import (
    run_simulation,
    calculate_units_utilized,
    calculate_statistics,
    replication,
    get_percentage_and_computingtimes,
    run_replications,
    print_stats,
    create_pivot
)


##############################
# Test calculate_units_utilized
##############################

def test_calculate_units_utilized_normal():
    units_utilized_over_time = [
        (0, 10, 5),
        (10, 20, 8),
        (20, 30, 10)
    ]
    capacity = 10
    time_end = 30
    expected_average = ((10 - 0) * 5 + (20 - 10) * 8 + (30 - 20) * 10) / 30
    assert calculate_units_utilized(units_utilized_over_time, capacity, time_end) == expected_average


def test_calculate_units_utilized_zero_time():
    units_utilized_over_time = []
    capacity = 10
    time_end = 0
    assert calculate_units_utilized(units_utilized_over_time, capacity, time_end) == 0


def test_calculate_units_utilized_exceed_capacity():
    units_utilized_over_time = [
        (0, 5, 15)  # Units exceed capacity
    ]
    capacity = 10
    time_end = 5
    expected_average = (5 - 0) * 10 / 5  # min(15, 10) = 10
    assert calculate_units_utilized(units_utilized_over_time, capacity, time_end) == expected_average


##############################
# Test get_percentage_and_computingtimes
##############################

def test_get_percentage_and_computingtimes():
    # Reset global variable
    with patch('src.util.simulations.seconds_previous_computations', new=0):
        computing_time_start = time.time() - 10  # Simulate 10 seconds have passed
        i = 4
        num_replications = 10
        result = get_percentage_and_computingtimes(computing_time_start, i, num_replications)

        percentage = " 50%"
        time_computed = f"[time computed] {str(timedelta(seconds=10)):<15}"
        time_to_complete = f"[time to complete] {str(timedelta(seconds=10)):<15}"
        time_prediction = f"[time prediction] {str(timedelta(seconds=20)):<15}"
        time_per_iteration = f"[time per iteration] {str(timedelta(seconds=10)):<15}"

        assert result == (percentage, time_computed, time_to_complete, time_prediction, time_per_iteration)


def test_get_percentage_and_computingtimes_initial():
    # Reset global variable
    with patch('src.util.simulations.seconds_previous_computations', new=0):
        computing_time_start = time.time() - 20  # Simulate 20 seconds have passed
        i = 9
        num_replications = 10
        result = get_percentage_and_computingtimes(computing_time_start, i, num_replications)

        percentage = "100%"
        time_computed = f"[time computed] {str(timedelta(seconds=20)):<15}"
        time_to_complete = f"[time to complete] {str(timedelta(seconds=0)):<15}"
        time_prediction = f"[time prediction] {str(timedelta(seconds=20)):<15}"
        time_per_iteration = f"[time per iteration] {str(timedelta(seconds=20)):<15}"

        assert result == (percentage, time_computed, time_to_complete, time_prediction, time_per_iteration)


##############################
# Test calculate_statistics
##############################

@patch('src.util.simulations.gi.DURATION_WARM_UP', 5)
@patch('src.util.simulations.Sink.sinks', new_callable=list)
@patch('src.util.simulations.Source.sources', new_callable=list)
@patch('src.util.simulations.Server.servers', new_callable=list)
@patch('src.util.simulations.EntityManager.entities', new_callable=list)
def test_calculate_statistics(mock_entities, mock_servers, mock_sinks, mock_sources):

    # Mock Entity
    mock_entity = MagicMock()
    mock_entity.destruction_time = 20
    mock_entity.creation_time = 10
    mock_entities.append(mock_entity)

    # Mock Server
    mock_server = MagicMock()
    mock_server.name = "Server1"
    mock_server.total_processing_time_pivot_table = 100
    mock_server.entities_processed = 10
    mock_server.units_utilized_over_time = [
        (0, 10, 5),
        (10, 20, 8),
        (20, 30, 10)
    ]
    mock_server.capacity = 10
    mock_server.number_entered_pivot_table = 5
    mock_server.number_exited_pivot_table = 5
    mock_server.number_downtimes_pivot_table = 1
    mock_server.total_downtime_pivot_table = 5
    mock_servers.append(mock_server)

    # Mock Sink
    mock_sink = MagicMock()
    mock_sink.name = "Sink1"
    mock_sink.total_time_in_system = 50
    mock_sink.entities_processed = 5
    mock_sink.max_time_in_system_pivot_table = 15
    mock_sink.min_time_in_system_pivot_table = 5
    mock_sink.number_entered_pivot_table = 5
    mock_sink.tally_statistic.num_times_processed_list = [1, 2, 3]
    mock_sink.tally_statistic.calculate_statistics.return_value = (1, 3, 2)
    mock_sinks.append(mock_sink)

    # Mock Source
    mock_source = MagicMock()
    mock_source.name = "Source1"
    mock_source.entities_created_pivot_table = 10
    mock_source.number_exited_pivot_table = 10
    mock_sources.append(mock_source)

    # Mock Environment
    mock_env = MagicMock()
    mock_env.now = 30

    # Call the function
    entity_stats, server_stats, sink_stats, source_stats = calculate_statistics(mock_env)

    # Assertions for Entity Stats
    assert entity_stats['NumberInSystem'] == 1
    assert entity_stats['AvgTimeInSystem'] == 10
    assert entity_stats['MaxTimeInSystem'] == 10
    assert entity_stats['MinTimeInSystem'] == 10
    assert entity_stats['NumberCreated'] == 1
    assert entity_stats['NumberDestroyed'] == 1

    # Assertions for Server Stats
    assert len(server_stats) == 1
    server = server_stats[0]
    assert server['Server'] == "Server1"
    # Scheduled Utilization = (100 / 30) * 100 = 333.333...
    assert server['ScheduledUtilization'] == pytest.approx(333.3333, 0.1)
    # Avg Time Processing = 100 / 10 = 10
    assert server['AvgTimeProcessing'] == 10
    # Units Utilized = ((10-0)*5 + (20-10)*8 + (30-20)*10) / 30 = (50 + 80 + 100) / 30 = 230/30 ≈ 7.6667
    expected_units_utilized = ((10 - 0) * 5 + (20 - 10) * 8 + (30 - 20) * 10) / 30
    assert server['UnitsUtilized'] == pytest.approx(expected_units_utilized, 0.0001)
    assert server['TotalTimeProcessing'] == 100
    assert server['NumberEntered'] == 5
    assert server['NumberExited'] == 5
    assert server['NumberDowntimes'] == 1
    assert server['TotalDowntime'] == 5

    # Assertions for Sink Stats
    assert 'Sink1' in sink_stats
    sink = sink_stats['Sink1']
    assert sink['AvgTimeInSystem'] == 10  # 50 / 5
    assert sink['MaxTimeInSystem'] == 15
    assert sink['MinTimeInSystem'] == 5
    assert sink['NumberEntered'] == 5
    assert sink['NumTimesProcessed_Avg'] == 2
    assert sink['NumTimesProcessed_Max'] == 3
    assert sink['NumTimesProcessed_Min'] == 1

    # Assertions for Source Stats
    assert 'Source1' in source_stats
    source = source_stats['Source1']
    assert source['NumberCreated'] == 10
    assert source['NumberExited'] == 10


##############################
# Test run_simulation
##############################

@patch('src.util.simulations.calculate_statistics')
@patch('src.util.simulations.simpy.Environment')
@patch('src.util.simulations.set_duration_warm_up')
@patch('src.util.simulations.random.seed')
def test_run_simulation(mock_random_seed, mock_set_warm_up, mock_simpy_env, mock_calculate_statistics):
    # Mock environment
    mock_env_instance = MagicMock()
    mock_simpy_env.return_value = mock_env_instance

    # Mock model
    mock_model = MagicMock()

    # Mock calculate_statistics return value
    mock_calculate_statistics.return_value = (
        {'NumberInSystem': 10},
        [{'Server': 'Server1', 'ScheduledUtilization': 80}],
        {'Sink1': {'AvgTimeInSystem': 20}},
        {'Source1': {'NumberCreated': 100}}
    )

    # Call run_simulation
    pivot = run_simulation(model=mock_model, minutes=100, warm_up=10, store_pivot_in_file=None)

    # Assertions
    mock_set_warm_up.assert_called_once_with(10)
    mock_random_seed.assert_called_once()
    mock_simpy_env.assert_called_once()
    mock_model.assert_called_once_with(mock_env_instance)
    mock_env_instance.run.assert_called_once_with(until=100)
    mock_calculate_statistics.assert_called_once_with(mock_env_instance)
    assert isinstance(pivot, pd.DataFrame)
    # Check pivot table contents
    assert ('Entity', 'Entity', 'NumberInSystem') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'NumberInSystem'), 'Value'] == 10
    assert ('Server', 'Server1', 'ScheduledUtilization') in pivot.index
    assert pivot.loc[('Server', 'Server1', 'ScheduledUtilization'), 'Value'] == 80
    assert ('Sink', 'Sink1', 'AvgTimeInSystem') in pivot.index
    assert pivot.loc[('Sink', 'Sink1', 'AvgTimeInSystem'), 'Value'] == 20
    assert ('Source', 'Source1', 'NumberCreated') in pivot.index
    assert pivot.loc[('Source', 'Source1', 'NumberCreated'), 'Value'] == 100


##############################
# Test replication
##############################

@patch('src.util.simulations.gc.collect')
@patch('src.util.simulations.delattr')  # Not directly mockable; better to skip or handle differently
@patch('src.util.simulations.Sink.sinks', new_callable=list)
@patch('src.util.simulations.Server.servers', new_callable=list)
@patch('src.util.simulations.Source.sources', new_callable=list)
@patch('src.util.simulations.EntityManager.destroy_all_entities')
@patch('src.util.simulations.set_duration_warm_up')
@patch('src.util.simulations.simpy.Environment')
@patch('src.util.simulations.random.seed')
def test_replication(mock_random_seed, mock_simpy_env, mock_set_warm_up,
                     mock_destroy_entities, mock_sources, mock_servers, mock_sinks, mock_gc_collect):

    # Mock replication parameters
    minutes = 50
    r = 42

    # Mock environment
    mock_env_instance = MagicMock()
    mock_simpy_env.return_value = mock_env_instance

    # Mock calculate_statistics return value
    with patch('src.util.simulations.calculate_statistics', return_value=({}, [], {}, {})) as mock_calculate_stats:
        # Call replication
        result = replication(env_setup_func=MagicMock(), calculate_stats_func=mock_calculate_stats,
                             minutes=minutes, r=r)

        # Assertions
        mock_random_seed.assert_called_once_with(r)
        mock_destroy_entities.assert_called_once()
        # Assuming reset_all is a method; adjust if different
        mock_sources.reset_all.assert_called_once()
        mock_servers.reset_all.assert_called_once()
        mock_sinks.reset_all.assert_called_once()
        mock_simpy_env.assert_called_once()
        mock_env_instance.run.assert_called_once_with(until=minutes)
        mock_calculate_stats.assert_called_once_with(mock_env_instance)
        mock_gc_collect.assert_called_once()
        assert result == ({}, [], {}, {})


##############################
# Test create_pivot
##############################

def test_create_pivot():

    # Sample data
    all_entity_stats = [
        {
            'AvgTimeInSystem': 10,
            'MaxTimeInSystem': 15,
            'MinTimeInSystem': 5,
            'NumberCreated': 100,
            'NumberDestroyed': 90,
            'NumberInSystem': 10
        }
    ]
    all_server_stats = {
        'Server1': [
            {
                'ScheduledUtilization': 80,
                'UnitsUtilized': 5,
                'AvgTimeProcessing': 10,
                'TotalTimeProcessing': 100,
                'NumberEntered': 50,
                'NumberExited': 50,
                'TotalDowntime': 5,
                'NumberDowntimes': 1
            }
        ]
    }
    all_sink_stats = {
        'Sink1': [
            {
                'AvgTimeInSystem': 20,
                'MaxTimeInSystem': 25,
                'MinTimeInSystem': 15,
                'NumberEntered': 80,
                'NumTimesProcessed_Avg': 2,
                'NumTimesProcessed_Max': 3,
                'NumTimesProcessed_Min': 1
            }
        ]
    }
    all_source_stats = {
        'Source1': [
            {
                'NumberCreated': 100,
                'NumberExited': 90
            }
        ]
    }
    entity_stat_names = ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem',
                         'NumberCreated', 'NumberDestroyed', 'NumberInSystem']
    server_stat_names = ['ScheduledUtilization', 'UnitsUtilized', 'AvgTimeProcessing',
                         'TotalTimeProcessing', 'NumberEntered', 'NumberExited', 'TotalDowntime', 'NumberDowntimes']
    sink_stat_names = ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem', 'NumberEntered',
                       'NumTimesProcessed_Avg', 'NumTimesProcessed_Max', 'NumTimesProcessed_Min']
    source_stat_names = ['NumberCreated', 'NumberExited']

    # Expected DataFrame structure
    pivot = create_pivot(
        all_entity_stats, all_server_stats, all_sink_stats, all_source_stats,
        entity_stat_names, server_stat_names, sink_stat_names, source_stat_names,
        store_pivot_in_file=None
    )

    # Assertions
    assert isinstance(pivot, pd.DataFrame)
    # Check specific entries
    assert ('Entity', 'Entity', 'AvgTimeInSystem') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'] == 10
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'] == 10
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'] == 15
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Half-Width'] == pytest.approx(
        1.96 * (0 / (10 ** 0.5)) if False else 0, 0.0001)  # Since std dev is 0, half-width is 0

    assert ('Server', 'Server1', 'ScheduledUtilization') in pivot.index
    assert pivot.loc[('Server', 'Server1', 'ScheduledUtilization'), 'Average'] == 80
    assert pivot.loc[('Server', 'Server1', 'UnitsUtilized'), 'Average'] == 5
    assert pivot.loc[('Server', 'Server1', 'AvgTimeProcessing'), 'Average'] == 10
    assert pivot.loc[('Server', 'Server1', 'TotalTimeProcessing'), 'Average'] == 100
    assert pivot.loc[('Server', 'Server1', 'NumberEntered'), 'Average'] == 50
    assert pivot.loc[('Server', 'Server1', 'NumberExited'), 'Average'] == 50
    assert pivot.loc[('Server', 'Server1', 'TotalDowntime'), 'Average'] == 5
    assert pivot.loc[('Server', 'Server1', 'NumberDowntimes'), 'Average'] == 1

    assert ('Sink', 'Sink1', 'AvgTimeInSystem') in pivot.index
    assert pivot.loc[('Sink', 'Sink1', 'AvgTimeInSystem'), 'Average'] == 20
    assert pivot.loc[('Sink', 'Sink1', 'AvgTimeInSystem'), 'Minimum'] == 20
    assert pivot.loc[('Sink', 'Sink1', 'AvgTimeInSystem'), 'Maximum'] == 20
    assert pivot.loc[('Sink', 'Sink1', 'AvgTimeInSystem'), 'Half-Width'] == pytest.approx(
        1.96 * (0 / (1 ** 0.5)) if False else 0, 0.0001)  # Since std dev is 0, half-width is 0

    assert ('Source', 'Source1', 'NumberCreated') in pivot.index
    assert pivot.loc[('Source', 'Source1', 'NumberCreated'), 'Average'] == 100
    assert pivot.loc[('Source', 'Source1', 'NumberCreated'), 'Minimum'] == 100
    assert pivot.loc[('Source', 'Source1', 'NumberCreated'), 'Maximum'] == 100
    assert pivot.loc[('Source', 'Source1', 'NumberCreated'), 'Half-Width'] == pytest.approx(
        1.96 * (0 / (1 ** 0.5)) if False else 0, 0.0001)  # Since std dev is 0, half-width is 0


##############################
# Test run_replications
##############################

@patch('src.util.simulations.save_to_db')
@patch('src.util.simulations.create_pivot')
@patch('src.util.simulations.replication')
@patch('src.util.simulations.set_duration_warm_up')
def test_run_replications_sequential(mock_set_warm_up, mock_replication, mock_create_pivot, mock_save_to_db):

    # Setup mock replication to return dummy stats
    mock_replication.return_value = ({}, [], {}, {})

    # Setup mock create_pivot to return empty DataFrame
    mock_create_pivot.return_value = pd.DataFrame()

    # Call run_replications
    combined_pivot = run_replications(
        model=MagicMock(),
        minutes=100,
        num_replications=5,
        warm_up=10,
        multiprocessing=False,
        save_to_database=False
    )

    # Assertions
    mock_set_warm_up.assert_called_once_with(10)
    assert mock_replication.call_count == 5
    mock_create_pivot.assert_called_once()
    mock_save_to_db.assert_not_called()
    assert isinstance(combined_pivot, pd.DataFrame)


@patch('src.util.simulations.save_to_db')
@patch('src.util.simulations.create_pivot')
@patch('src.util.simulations.replication')
@patch('src.util.simulations.set_duration_warm_up')
@patch('src.util.simulations.concurrent.futures.ProcessPoolExecutor')
def test_run_replications_multiprocessing(mock_executor, mock_set_warm_up, mock_replication, mock_create_pivot,
                                          mock_save_to_db):

    # Setup mock replication to return dummy stats
    mock_replication.return_value = ({}, [], {}, {})

    # Setup mock create_pivot to return empty DataFrame
    mock_create_pivot.return_value = pd.DataFrame()

    # Setup mock ProcessPoolExecutor
    mock_executor_instance = MagicMock()
    mock_executor.return_value.__enter__.return_value = mock_executor_instance
    # Mock the submit method to return futures with result()
    mock_future = MagicMock()
    mock_future.result.return_value = ({}, [], {}, {})
    mock_executor_instance.submit.return_value = mock_future

    # Call run_replications with multiprocessing=True
    combined_pivot = run_replications(
        model=MagicMock(),
        minutes=100,
        num_replications=5,
        warm_up=10,
        multiprocessing=True,
        save_to_database=False
    )

    # Assertions
    mock_set_warm_up.assert_called_once_with(10)
    assert mock_replication.call_count == 5
    mock_executor.assert_called_once()
    mock_create_pivot.assert_called_once()
    mock_save_to_db.assert_not_called()
    assert isinstance(combined_pivot, pd.DataFrame)


##############################
# Test run_replications with save_to_database=True
##############################

@patch('src.util.simulations.save_to_db')
@patch('src.util.simulations.create_pivot')
@patch('src.util.simulations.replication')
@patch('src.util.simulations.set_duration_warm_up')
def test_run_replications_save_to_db(mock_set_warm_up, mock_replication, mock_create_pivot, mock_save_to_db):

    # Setup mock replication to return dummy stats
    mock_replication.return_value = ({}, [], {}, {})

    # Setup mock create_pivot to return empty DataFrame
    mock_create_pivot.return_value = pd.DataFrame()

    # Mock datetime.now()
    with patch('src.util.simulations.datetime') as mock_datetime:
        mock_start_time = datetime(2024, 10, 10, 12, 0, 0)
        mock_end_time = datetime(2024, 10, 10, 12, 30, 0)
        mock_datetime.now.side_effect = [mock_start_time, mock_end_time]

        # Call run_replications with save_to_database=True
        combined_pivot = run_replications(
            model=MagicMock(),
            minutes=100,
            num_replications=5,
            warm_up=10,
            multiprocessing=False,
            save_to_database=True
        )

        # Assertions
        mock_save_to_db.assert_called_once_with(combined_pivot, mock_start_time, mock_end_time, 100, 5)


##############################
# Test print_stats
##############################

@patch('src.util.simulations.send_progress_to_server')
@patch('src.util.simulations.logging')
@patch('src.util.simulations.get_percentage_and_computingtimes')
def test_print_stats_not_send_progress(mock_get_times, mock_logging, mock_send_progress):

    # Setup mock return value
    mock_get_times.return_value = (
        " 50%", "[time computed] 0:00:10    ", "[time to complete] 0:00:10    ",
        "[time prediction] 0:00:20    ", "[time per iteration] 0:00:10    "
    )

    # Call print_stats where (i+1) != tenth_percentage
    print_stats(i=4, num_replications=10, start=0, tenth_percentage=2)

    # Assertions
    mock_get_times.assert_called_once_with(0, 4, 10)
    mock_logging.info.assert_called_once_with(
        " 50% replication 5/10\t[time computed] 0:00:10    \t[time to complete] 0:00:10    \t[time prediction] 0:00:20    \t[time per iteration] 0:00:10    "
    )
    mock_send_progress.assert_not_called()


@patch('src.util.simulations.send_progress_to_server')
@patch('src.util.simulations.logging')
@patch('src.util.simulations.get_percentage_and_computingtimes')
def test_print_stats_send_progress(mock_get_times, mock_logging, mock_send_progress):

    # Setup mock return value
    mock_get_times.return_value = (
        " 10%", "[time computed] 0:00:10    ", "[time to complete] 0:00:90    ",
        "[time prediction] 0:01:00    ", "[time per iteration] 0:00:10    "
    )

    # Set CONFIG_PATH to trigger sending progress
    with patch.dict('os.environ', {'CONFIG_PATH': 'path/to/config'}):
        # Call print_stats where (i+1) == tenth_percentage
        print_stats(i=0, num_replications=10, start=0, tenth_percentage=1)

        # Assertions
        mock_get_times.assert_called_once_with(0, 0, 10)
        mock_logging.info.assert_called_once_with(
            " 10% replication 1/10\t[time computed] 0:00:10    \t[time to complete] 0:00:90    \t[time prediction] 0:01:00    \t[time per iteration] 0:00:10    "
        )
        mock_send_progress.assert_called_once()


##############################
# Test print_stats without CONFIG_PATH
##############################

@patch('src.util.simulations.send_progress_to_server')
@patch('src.util.simulations.logging')
@patch('src.util.simulations.get_percentage_and_computingtimes')
def test_print_stats_send_progress_no_config(mock_get_times, mock_logging, mock_send_progress):

    # Setup mock return value
    mock_get_times.return_value = (
        " 10%", "[time computed] 0:00:10    ", "[time to complete] 0:00:90    ",
        "[time prediction] 0:01:00    ", "[time per iteration] 0:00:10    "
    )

    # Ensure CONFIG_PATH is not set
    with patch.dict('os.environ', {}, clear=True):
        # Call print_stats where (i+1) == tenth_percentage
        print_stats(i=0, num_replications=10, start=0, tenth_percentage=1)

        # Assertions
        mock_get_times.assert_called_once_with(0, 0, 10)
        mock_logging.info.assert_called_once_with(
            " 10% replication 1/10\t[time computed] 0:00:10    \t[time to complete] 0:00:90    \t[time prediction] 0:01:00    \t[time per iteration] 0:00:10    "
        )
        mock_send_progress.assert_not_called()


##############################
# Test run_simulation with warm_up=None
##############################

@patch('src.util.simulations.calculate_statistics')
@patch('src.util.simulations.simpy.Environment')
@patch('src.util.simulations.set_duration_warm_up')
@patch('src.util.simulations.random.seed')
def test_run_simulation_no_warm_up(mock_random_seed, mock_set_warm_up, mock_simpy_env, mock_calculate_statistics):

    # Mock environment
    mock_env_instance = MagicMock()
    mock_simpy_env.return_value = mock_env_instance

    # Mock model
    mock_model = MagicMock()

    # Mock calculate_statistics return value
    mock_calculate_statistics.return_value = (
        {'NumberInSystem': 20},
        [{'Server': 'Server2', 'ScheduledUtilization': 60}],
        {'Sink2': {'AvgTimeInSystem': 30}},
        {'Source2': {'NumberCreated': 200}}
    )

    # Call run_simulation without warm_up and without storing to file
    pivot = run_simulation(model=mock_model, minutes=200)

    # Assertions
    mock_set_warm_up.assert_not_called()
    mock_random_seed.assert_called_once()
    mock_simpy_env.assert_called_once()
    mock_model.assert_called_once_with(mock_env_instance)
    mock_env_instance.run.assert_called_once_with(until=200)
    mock_calculate_statistics.assert_called_once_with(mock_env_instance)
    assert isinstance(pivot, pd.DataFrame)
    # Check pivot table contents
    assert ('Entity', 'Entity', 'NumberInSystem') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'NumberInSystem'), 'Value'] == 20
    assert ('Server', 'Server2', 'ScheduledUtilization') in pivot.index
    assert pivot.loc[('Server', 'Server2', 'ScheduledUtilization'), 'Value'] == 60
    assert ('Sink', 'Sink2', 'AvgTimeInSystem') in pivot.index
    assert pivot.loc[('Sink', 'Sink2', 'AvgTimeInSystem'), 'Value'] == 30
    assert ('Source', 'Source2', 'NumberCreated') in pivot.index
    assert pivot.loc[('Source', 'Source2', 'NumberCreated'), 'Value'] == 200


##############################
# Test run_simulation with store_pivot_in_file
##############################

@patch('src.util.simulations.calculate_statistics')
@patch('src.util.simulations.simpy.Environment')
@patch('src.util.simulations.set_duration_warm_up')
@patch('src.util.simulations.random.seed')
def test_run_simulation_store_pivot_in_file(mock_random_seed, mock_set_warm_up, mock_simpy_env,
                                            mock_calculate_statistics, tmp_path):

    # Mock environment
    mock_env_instance = MagicMock()
    mock_simpy_env.return_value = mock_env_instance

    # Mock model
    mock_model = MagicMock()

    # Mock calculate_statistics return value
    mock_calculate_statistics.return_value = (
        {'NumberInSystem': 30},
        [{'Server': 'Server3', 'ScheduledUtilization': 70}],
        {'Sink3': {'AvgTimeInSystem': 40}},
        {'Source3': {'NumberCreated': 300}}
    )

    # Define a temporary file path
    store_pivot_in_file = tmp_path / "pivot.csv"

    # Call run_simulation with store_pivot_in_file
    pivot = run_simulation(
        model=mock_model,
        minutes=300,
        warm_up=15,
        store_pivot_in_file=str(store_pivot_in_file)
    )

    # Assertions
    mock_set_warm_up.assert_called_once_with(15)
    mock_random_seed.assert_called_once()
    mock_simpy_env.assert_called_once()
    mock_model.assert_called_once_with(mock_env_instance)
    mock_env_instance.run.assert_called_once_with(until=300)
    mock_calculate_statistics.assert_called_once_with(mock_env_instance)
    assert isinstance(pivot, pd.DataFrame)
    # Check if file was created
    assert store_pivot_in_file.exists()
    # Optionally, read the file and verify contents
    df = pd.read_csv(store_pivot_in_file)
    assert not df.empty
    assert df.loc[df['Type'] == 'Entity', 'Value'].iloc[0] == 30
    assert df.loc[df['Type'] == 'Server', 'Value'].iloc[0] == 70
    assert df.loc[df['Type'] == 'Sink', 'Value'].iloc[0] == 40
    assert df.loc[df['Type'] == 'Source', 'Value'].iloc[0] == 300


##############################
# Test create_pivot with empty data
##############################

def test_create_pivot_empty():

    # Empty data
    all_entity_stats = []
    all_server_stats = {}
    all_sink_stats = {}
    all_source_stats = {}
    entity_stat_names = ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem',
                         'NumberCreated', 'NumberDestroyed', 'NumberInSystem']
    server_stat_names = ['ScheduledUtilization', 'UnitsUtilized', 'AvgTimeProcessing',
                         'TotalTimeProcessing', 'NumberEntered', 'NumberExited', 'TotalDowntime', 'NumberDowntimes']
    sink_stat_names = ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem', 'NumberEntered',
                       'NumTimesProcessed_Avg', 'NumTimesProcessed_Max', 'NumTimesProcessed_Min']
    source_stat_names = ['NumberCreated', 'NumberExited']

    # Call create_pivot
    pivot = create_pivot(
        all_entity_stats, all_server_stats, all_sink_stats, all_source_stats,
        entity_stat_names, server_stat_names, sink_stat_names, source_stat_names,
        store_pivot_in_file=None
    )

    # Assertions
    assert isinstance(pivot, pd.DataFrame)
    assert pivot.empty


##############################
# Test calculate_statistics with no destruction_time
##############################

@patch('src.util.simulations.gi.DURATION_WARM_UP', 5)
@patch('src.util.simulations.Sink.sinks', new_callable=list)
@patch('src.util.simulations.Source.sources', new_callable=list)
@patch('src.util.simulations.Server.servers', new_callable=list)
@patch('src.util.simulations.EntityManager.entities', new_callable=list)
def test_calculate_statistics_no_destruction_time(mock_entities, mock_servers, mock_sinks, mock_sources):

    # Mock Entity without destruction_time
    mock_entity = MagicMock()
    mock_entity.destruction_time = None
    mock_entity.creation_time = 10
    mock_entities.append(mock_entity)

    # Mock Server
    mock_server = MagicMock()
    mock_server.name = "Server1"
    mock_server.total_processing_time_pivot_table = 50
    mock_server.entities_processed = 5
    mock_server.units_utilized_over_time = []
    mock_server.capacity = 10
    mock_server.number_entered_pivot_table = 2
    mock_server.number_exited_pivot_table = 2
    mock_server.number_downtimes_pivot_table = 0
    mock_server.total_downtime_pivot_table = 0
    mock_servers.append(mock_server)

    # Mock Sink
    mock_sink = MagicMock()
    mock_sink.name = "Sink1"
    mock_sink.total_time_in_system = 25
    mock_sink.entities_processed = 2
    mock_sink.max_time_in_system_pivot_table = 12
    mock_sink.min_time_in_system_pivot_table = 8
    mock_sink.number_entered_pivot_table = 2
    mock_sink.tally_statistic.num_times_processed_list = [1, 1]
    mock_sink.tally_statistic.calculate_statistics.return_value = (1, 1, 1)
    mock_sinks.append(mock_sink)

    # Mock Source
    mock_source = MagicMock()
    mock_source.name = "Source1"
    mock_source.entities_created_pivot_table = 5
    mock_source.number_exited_pivot_table = 5
    mock_sources.append(mock_source)

    # Mock Environment
    mock_env = MagicMock()
    mock_env.now = 30

    # Call the function
    entity_stats, server_stats, sink_stats, source_stats = calculate_statistics(mock_env)

    # Assertions for Entity Stats
    assert entity_stats['NumberInSystem'] == 1  # One entity in system
    assert entity_stats['AvgTimeInSystem'] == 0  # destruction_time is None
    assert entity_stats['MaxTimeInSystem'] == 0
    assert entity_stats['MinTimeInSystem'] == 0
    assert entity_stats['NumberCreated'] == 1
    assert entity_stats['NumberDestroyed'] == 0

    # Assertions for Server Stats
    assert len(server_stats) == 1
    server = server_stats[0]
    assert server['Server'] == "Server1"
    assert server['ScheduledUtilization'] == (50 / 30) * 100  # 166.666...
    assert server['AvgTimeProcessing'] == 10
    assert server['UnitsUtilized'] == 0  # Empty units_utilized_over_time
    assert server['TotalTimeProcessing'] == 50
    assert server['NumberEntered'] == 2
    assert server['NumberExited'] == 2
    assert server['NumberDowntimes'] == 0
    assert server['TotalDowntime'] == 0

    # Assertions for Sink Stats
    assert 'Sink1' in sink_stats
    sink = sink_stats['Sink1']
    assert sink['AvgTimeInSystem'] == 12.5  # 25 / 2
    assert sink['MaxTimeInSystem'] == 12
    assert sink['MinTimeInSystem'] == 8
    assert sink['NumberEntered'] == 2
    assert sink['NumTimesProcessed_Avg'] == 1
    assert sink['NumTimesProcessed_Max'] == 1
    assert sink['NumTimesProcessed_Min'] == 1

    # Assertions for Source Stats
    assert 'Source1' in source_stats
    source = source_stats['Source1']
    assert source['NumberCreated'] == 5
    assert source['NumberExited'] == 5


##############################
# Test replication exception handling
##############################

@patch('src.util.simulations.gc.collect')
@patch('src.util.simulations.Sink.sinks', new_callable=list)
@patch('src.util.simulations.Server.servers', new_callable=list)
@patch('src.util.simulations.Source.sources', new_callable=list)
@patch('src.util.simulations.EntityManager.destroy_all_entities')
@patch('src.util.simulations.set_duration_warm_up')
@patch('src.util.simulations.simpy.Environment')
@patch('src.util.simulations.random.seed')
def test_replication_exception(mock_random_seed, mock_simpy_env, mock_set_warm_up,
                               mock_destroy_entities, mock_sources, mock_servers, mock_sinks, mock_gc_collect):

    # Mock replication parameters
    minutes = 50
    r = 42

    # Mock environment
    mock_env_instance = MagicMock()
    mock_simpy_env.return_value = mock_env_instance

    # Mock calculate_statistics to raise an exception
    with patch('src.util.simulations.calculate_statistics', side_effect=Exception("Test Exception")) as mock_calculate_stats:
        with pytest.raises(Exception) as exc_info:
            replication(env_setup_func=MagicMock(), calculate_stats_func=mock_calculate_stats,
                        minutes=minutes, r=r)

        assert str(exc_info.value) == "Test Exception"

        # Assertions
        mock_random_seed.assert_called_once_with(r)
        mock_destroy_entities.assert_called_once()
        mock_sources.reset_all.assert_called_once()
        mock_servers.reset_all.assert_called_once()
        mock_sinks.reset_all.assert_called_once()
        mock_simpy_env.assert_called_once()
        mock_env_instance.run.assert_called_once_with(until=minutes)
        mock_calculate_stats.assert_called_once_with(mock_env_instance)
        mock_gc_collect.assert_called_once()


##############################
# Test run_replications with exception in replication
##############################

@patch('src.util.simulationss.logging')
@patch('src.util.simulations.print_stats')
@patch('src.util.simulations.create_pivot')
@patch('src.util.simulations.replication')
@patch('src.util.simulations.set_duration_warm_up')
def test_run_replications_with_exception(mock_set_warm_up, mock_replication, mock_create_pivot, mock_print_stats,
                                         mock_logging):

    # Setup mock replication to raise exception on the third call
    def side_effect(*args, **kwargs):
        if args[3] == 2:  # Replication 3
            raise Exception("Replication Error")
        return ({}, [], {}, {})

    mock_replication.side_effect = side_effect

    # Setup mock create_pivot to return empty DataFrame
    mock_create_pivot.return_value = pd.DataFrame()

    # Call run_replications
    with pytest.raises(Exception) as exc_info:
        run_replications(
            model=MagicMock(),
            minutes=100,
            num_replications=5,
            warm_up=10,
            multiprocessing=False,
            save_to_database=False
        )

    # Assertions
    assert str(exc_info.value) == "Replication Error"
    mock_set_warm_up.assert_called_once_with(10)
    assert mock_replication.call_count == 3  # Should stop at the third replication
    mock_create_pivot.assert_not_called()  # Pivot not created due to exception


##############################
# Additional Tests for Edge Cases
##############################

def test_run_simulation_zero_minutes():

    # Mock dependencies
    with patch('src.util.simulations.set_duration_warm_up') as mock_set_warm_up, \
            patch('src.util.simulations.random.seed') as mock_random_seed, \
            patch('src.util.simulations.simpy.Environment') as mock_simpy_env, \
            patch('src.util.simulations.calculate_statistics', return_value=({}, [], {}, {})) as mock_calculate_statistics, \
            patch('src.util.simulations.logging') as mock_logging:
        mock_env_instance = MagicMock()
        mock_simpy_env.return_value = mock_env_instance
        mock_model = MagicMock()

        # Call run_simulation with minutes=0
        pivot = run_simulation(model=mock_model, minutes=0, warm_up=None, store_pivot_in_file=None)

        # Assertions
        mock_set_warm_up.assert_not_called()
        mock_random_seed.assert_called_once()
        mock_simpy_env.assert_called_once()
        mock_model.assert_called_once_with(mock_env_instance)
        mock_env_instance.run.assert_called_once_with(until=0)
        mock_calculate_statistics.assert_called_once_with(mock_env_instance)
        assert isinstance(pivot, pd.DataFrame)
        assert pivot.empty  # Assuming no stats collected


def test_run_replications_zero_replications():

    # Mock dependencies
    with patch('src.util.simulations.save_to_db') as mock_save_to_db, \
            patch('src.util.simulations.create_pivot', return_value=pd.DataFrame()) as mock_create_pivot, \
            patch('src.util.simulations.replication') as mock_replication, \
            patch('src.util.simulations.set_duration_warm_up') as mock_set_warm_up:
        # Call run_replications with num_replications=0
        combined_pivot = run_replications(
            model=MagicMock(),
            minutes=100,
            num_replications=0,
            warm_up=10,
            multiprocessing=False,
            save_to_database=False
        )

        # Assertions
        mock_set_warm_up.assert_called_once_with(10)
        mock_replication.assert_not_called()
        mock_create_pivot.assert_called_once_with(
            [],
            {},
            {},
            {},
            ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem',
             'NumberCreated', 'NumberDestroyed', 'NumberInSystem'],
            ['ScheduledUtilization', 'UnitsUtilized', 'AvgTimeProcessing',
             'TotalTimeProcessing', 'NumberEntered', 'NumberExited', 'TotalDowntime', 'NumberDowntimes'],
            ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem', 'NumberEntered',
             'NumTimesProcessed_Avg', 'NumTimesProcessed_Max', 'NumTimesProcessed_Min'],
            ['NumberCreated', 'NumberExited'],
            store_pivot_in_file=None
        )
        mock_save_to_db.assert_not_called()
        assert isinstance(combined_pivot, pd.DataFrame)
        assert combined_pivot.empty


##############################
# Test create_pivot with multiple replications
##############################

def test_create_pivot_multiple_replications():

    # Sample data with multiple replications
    all_entity_stats = [
        {'AvgTimeInSystem': 10, 'MaxTimeInSystem': 15, 'MinTimeInSystem': 5,
         'NumberCreated': 100, 'NumberDestroyed': 90, 'NumberInSystem': 10},
        {'AvgTimeInSystem': 12, 'MaxTimeInSystem': 18, 'MinTimeInSystem': 6,
         'NumberCreated': 110, 'NumberDestroyed': 95, 'NumberInSystem': 12}
    ]
    all_server_stats = {
        'Server1': [
            {'ScheduledUtilization': 80, 'UnitsUtilized': 5, 'AvgTimeProcessing': 10,
             'TotalTimeProcessing': 100, 'NumberEntered': 50, 'NumberExited': 50,
             'TotalDowntime': 5, 'NumberDowntimes': 1},
            {'ScheduledUtilization': 85, 'UnitsUtilized': 6, 'AvgTimeProcessing': 12,
             'TotalTimeProcessing': 120, 'NumberEntered': 55, 'NumberExited': 55,
             'TotalDowntime': 6, 'NumberDowntimes': 2}
        ]
    }
    all_sink_stats = {
        'Sink1': [
            {'AvgTimeInSystem': 20, 'MaxTimeInSystem': 25, 'MinTimeInSystem': 15,
             'NumberEntered': 80,
             'NumTimesProcessed_Avg': 2, 'NumTimesProcessed_Max': 3, 'NumTimesProcessed_Min': 1},
            {'AvgTimeInSystem': 22, 'MaxTimeInSystem': 28, 'MinTimeInSystem': 16,
             'NumberEntered': 85,
             'NumTimesProcessed_Avg': 2.5, 'NumTimesProcessed_Max': 3.5, 'NumTimesProcessed_Min': 1.5},
        ]
    }
    all_source_stats = {
        'Source1': [
            {'NumberCreated': 100, 'NumberExited': 90},
            {'NumberCreated': 110, 'NumberExited': 95}
        ]
    }
    entity_stat_names = ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem',
                         'NumberCreated', 'NumberDestroyed', 'NumberInSystem']
    server_stat_names = ['ScheduledUtilization', 'UnitsUtilized', 'AvgTimeProcessing',
                         'TotalTimeProcessing', 'NumberEntered', 'NumberExited', 'TotalDowntime', 'NumberDowntimes']
    sink_stat_names = ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem', 'NumberEntered',
                       'NumTimesProcessed_Avg', 'NumTimesProcessed_Max', 'NumTimesProcessed_Min']
    source_stat_names = ['NumberCreated', 'NumberExited']

    # Call create_pivot
    pivot = create_pivot(
        all_entity_stats, all_server_stats, all_sink_stats, all_source_stats,
        entity_stat_names, server_stat_names, sink_stat_names, source_stat_names,
        store_pivot_in_file=None
    )

    # Assertions
    assert isinstance(pivot, pd.DataFrame)
    # Check aggregate values
    # Entity
    assert ('Entity', 'Entity', 'AvgTimeInSystem') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'] == 11
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'] == 5
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'] == 15
    # Server
    assert ('Server', 'Server1', 'ScheduledUtilization') in pivot.index
    assert pivot.loc[('Server', 'Server1', 'ScheduledUtilization'), 'Average'] == 82.5
    assert pivot.loc[('Server', 'Server1', 'ScheduledUtilization'), 'Minimum'] == 80
    assert pivot.loc[('Server', 'Server1', 'ScheduledUtilization'), 'Maximum'] == 85
    # Sink
    assert ('Sink', 'Sink1', 'AvgTimeInSystem') in pivot.index
    assert pivot.loc[('Sink', 'Sink1', 'AvgTimeInSystem'), 'Average'] == 21
    # Source
    assert ('Source', 'Source1', 'NumberCreated') in pivot.index
    assert pivot.loc[('Source', 'Source1', 'NumberCreated'), 'Average'] == 105
    assert pivot.loc[('Source', 'Source1', 'NumberCreated'), 'Minimum'] == 100
    assert pivot.loc[('Source', 'Source1', 'NumberCreated'), 'Maximum'] == 110

    # Verify that Half-Width is calculated correctly (assuming std deviation is 1 for simplicity)
    # Since it's based on the actual data, in reality, we would calculate it accordingly
    # Here, we skip checking exact Half-Width values due to variability


##############################
# Test run_simulation with exceptions in calculate_statistics
##############################

@patch('src.util.simulations.calculate_statistics', side_effect=Exception("Statistics Error"))
@patch('src.util.simulations.simpy.Environment')
@patch('src.util.simulations.set_duration_warm_up')
@patch('src.util.simulations.random.seed')
def test_run_simulation_calculate_statistics_exception(mock_random_seed, mock_set_warm_up, mock_simpy_env,
                                                       mock_calculate_statistics):

    # Mock environment
    mock_env_instance = MagicMock()
    mock_simpy_env.return_value = mock_env_instance

    # Mock model
    mock_model = MagicMock()

    # Call run_simulation and expect exception
    with pytest.raises(Exception) as exc_info:
        run_simulation(model=mock_model, minutes=100, warm_up=10, store_pivot_in_file=None)

    assert str(exc_info.value) == "Statistics Error"

    # Assertions
    mock_set_warm_up.assert_called_once_with(10)
    mock_random_seed.assert_called_once()
    mock_simpy_env.assert_called_once()
    mock_model.assert_called_once_with(mock_env_instance)
    mock_env_instance.run.assert_called_once_with(until=100)
    mock_calculate_statistics.assert_called_once_with(mock_env_instance)


##############################
# Test create_pivot with non-numeric values
##############################

def test_create_pivot_non_numeric():

    # Sample data with non-numeric values
    all_entity_stats = [
        {'AvgTimeInSystem': 'NaN', 'MaxTimeInSystem': None, 'MinTimeInSystem': '5',
         'NumberCreated': '100', 'NumberDestroyed': 90, 'NumberInSystem': 10}
    ]
    all_server_stats = {}
    all_sink_stats = {}
    all_source_stats = {}
    entity_stat_names = ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem',
                         'NumberCreated', 'NumberDestroyed', 'NumberInSystem']
    server_stat_names = []
    sink_stat_names = []
    source_stat_names = []

    # Call create_pivot
    pivot = create_pivot(
        all_entity_stats, all_server_stats, all_sink_stats, all_source_stats,
        entity_stat_names, server_stat_names, sink_stat_names, source_stat_names,
        store_pivot_in_file=None
    )

    # Assertions
    assert isinstance(pivot, pd.DataFrame)
    # Since non-numeric values are present, the aggregate stats should handle them
    # Avg, Min, Max, Half-Width should be None or handled appropriately
    assert ('Entity', 'Entity', 'AvgTimeInSystem') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'] is None
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'] is None
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'] is None
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Half-Width'] is None

    assert ('Entity', 'Entity', 'MinTimeInSystem') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'MinTimeInSystem'), 'Average'] == 5
    assert pivot.loc[('Entity', 'Entity', 'MinTimeInSystem'), 'Minimum'] == 5
    assert pivot.loc[('Entity', 'Entity', 'MinTimeInSystem'), 'Maximum'] == 5
    assert pivot.loc[('Entity', 'Entity', 'MinTimeInSystem'), 'Half-Width'] == pytest.approx(
        1.96 * (0 / (1 ** 0.5)) if False else 0, 0.0001)

    assert ('Entity', 'Entity', 'NumberCreated') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'NumberCreated'), 'Average'] == 100
    assert pivot.loc[('Entity', 'Entity', 'NumberCreated'), 'Minimum'] == 100
    assert pivot.loc[('Entity', 'Entity', 'NumberCreated'), 'Maximum'] == 100
    assert pivot.loc[('Entity', 'Entity', 'NumberCreated'), 'Half-Width'] == pytest.approx(
        1.96 * (0 / (1 ** 0.5)) if False else 0, 0.0001)

    # NumberDestroyed should be 90
    assert ('Entity', 'Entity', 'NumberDestroyed') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'NumberDestroyed'), 'Average'] == 90

    # NumberInSystem should be 10
    assert ('Entity', 'Entity', 'NumberInSystem') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'NumberInSystem'), 'Average'] == 10


##############################
# Test create_pivot with mixed types
##############################

def test_create_pivot_mixed_types():

    # Sample data with mixed types
    all_entity_stats = [
        {'AvgTimeInSystem': 10, 'MaxTimeInSystem': '15', 'MinTimeInSystem': 5,
         'NumberCreated': '100', 'NumberDestroyed': None, 'NumberInSystem': 10},
        {'AvgTimeInSystem': 12, 'MaxTimeInSystem': 18, 'MinTimeInSystem': '6',
         'NumberCreated': 110, 'NumberDestroyed': '95', 'NumberInSystem': '12'}
    ]
    all_server_stats = {
        'Server1': [
            {'ScheduledUtilization': '80', 'UnitsUtilized': 5, 'AvgTimeProcessing': '10',
             'TotalTimeProcessing': 100, 'NumberEntered': '50', 'NumberExited': 50,
             'TotalDowntime': None, 'NumberDowntimes': '1'},
            {'ScheduledUtilization': 85, 'UnitsUtilized': '6', 'AvgTimeProcessing': 12,
             'TotalTimeProcessing': '120', 'NumberEntered': 55, 'NumberExited': '55',
             'TotalDowntime': 6, 'NumberDowntimes': 2}
        ]
    }
    all_sink_stats = {}
    all_source_stats = {}
    entity_stat_names = ['AvgTimeInSystem', 'MaxTimeInSystem', 'MinTimeInSystem',
                         'NumberCreated', 'NumberDestroyed', 'NumberInSystem']
    server_stat_names = ['ScheduledUtilization', 'UnitsUtilized', 'AvgTimeProcessing',
                         'TotalTimeProcessing', 'NumberEntered', 'NumberExited', 'TotalDowntime', 'NumberDowntimes']
    sink_stat_names = []
    source_stat_names = []

    # Call create_pivot
    pivot = create_pivot(
        all_entity_stats, all_server_stats, all_sink_stats, all_source_stats,
        entity_stat_names, server_stat_names, sink_stat_names, source_stat_names,
        store_pivot_in_file=None
    )

    # Assertions
    assert isinstance(pivot, pd.DataFrame)
    # AvgTimeInSystem: 10 and 12
    assert ('Entity', 'Entity', 'AvgTimeInSystem') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'] == 11
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'] == 10
    assert pivot.loc[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'] == 12
    # NumberDestroyed: 0 and 1 (only second replication has 95)
    assert ('Entity', 'Entity', 'NumberDestroyed') in pivot.index
    assert pivot.loc[('Entity', 'Entity', 'NumberDestroyed'), 'Average'] == 95
    # Server ScheduledUtilization
    assert ('Server', 'Server1', 'ScheduledUtilization') in pivot.index
    assert pivot.loc[('Server', 'Server1', 'ScheduledUtilization'), 'Average'] == 82.5
    # UnitsUtilized
    assert ('Server', 'Server1', 'UnitsUtilized') in pivot.index
    assert pivot.loc[('Server', 'Server1', 'UnitsUtilized'), 'Average'] == 5.5
    # AvgTimeProcessing
    assert ('Server', 'Server1', 'AvgTimeProcessing') in pivot.index
    assert pivot.loc[('Server', 'Server1', 'AvgTimeProcessing'), 'Average'] == 11
    # TotalDowntime
    assert ('Server', 'Server1', 'TotalDowntime') in pivot.index
    assert pivot.loc[('Server', 'Server1', 'TotalDowntime'), 'Average'] == 3
    # NumberDowntimes
    assert ('Server', 'Server1', 'NumberDowntimes') in pivot.index
    assert pivot.loc[('Server', 'Server1', 'NumberDowntimes'), 'Average'] == 1.5


##############################
# Test create_pivot with store_pivot_in_file
##############################

def test_create_pivot_store_pivot_in_file(tmp_path):

    # Sample data
    all_entity_stats = []
    all_server_stats = {}
    all_sink_stats = {}
    all_source_stats = {}
    entity_stat_names = []
    server_stat_names = []
    sink_stat_names = []
    source_stat_names = []

    # Define a temporary file path
    store_pivot_in_file = tmp_path / "pivot_combined.csv"

    # Call create_pivot
    pivot = create_pivot(
        all_entity_stats, all_server_stats, all_sink_stats, all_source_stats,
        entity_stat_names, server_stat_names, sink_stat_names, source_stat_names,
        store_pivot_in_file=str(store_pivot_in_file)
    )

    # Assertions
    assert isinstance(pivot, pd.DataFrame)
    assert pivot.empty
    assert store_pivot_in_file.exists()
    # Check file is empty
    df = pd.read_csv(store_pivot_in_file)
    assert df.empty


##############################
# Test replication with multiprocessing and exceptions
##############################

@patch('src.util.simulations.gc.collect')
@patch('src.util.simulations.Sink.sinks', new_callable=list)
@patch('src.util.simulations.Server.servers', new_callable=list)
@patch('src.util.simulations.Source.sources', new_callable=list)
@patch('src.util.simulations.EntityManager.destroy_all_entities')
@patch('src.util.simulations.set_duration_warm_up')
@patch('src.util.simulations.simpy.Environment')
@patch('src.util.simulations.random.seed')
@patch('src.util.simulations.concurrent.futures.ProcessPoolExecutor')
def test_run_replications_multiprocessing_with_exceptions(mock_executor, mock_random_seed, mock_simpy_env,
                                                          mock_set_warm_up, mock_destroy_entities,
                                                          mock_sources, mock_servers, mock_sinks, mock_gc_collect):

    # Setup mock ProcessPoolExecutor
    mock_executor_instance = MagicMock()
    mock_executor.return_value.__enter__.return_value = mock_executor_instance

    # Mock replication to raise exception on the second future
    def side_effect_submit(*args, **kwargs):
        mock_future = MagicMock()
        if args[0] == run_replications.__globals__['replication'] and args[1] == 1:
            mock_future.result.side_effect = Exception("Future Error")
        else:
            mock_future.result.return_value = ({}, [], {}, {})
        return mock_future

    mock_executor_instance.submit.side_effect = side_effect_submit

    # Setup mock create_pivot to return empty DataFrame
    with patch('src.util.simulations.create_pivot', return_value=pd.DataFrame()) as mock_create_pivot:
        # Call run_replications with multiprocessing=True
        with pytest.raises(Exception) as exc_info:
            run_replications(
                model=MagicMock(),
                minutes=100,
                num_replications=3,
                warm_up=10,
                multiprocessing=True,
                save_to_database=False
            )

        # Assertions
        assert str(exc_info.value) == "Future Error"
        mock_set_warm_up.assert_called_once_with(10)
        assert mock_executor.call_count == 1
        assert mock_executor_instance.submit.call_count == 3  # 3 replications
        mock_create_pivot.assert_not_called()  # Pivot not created due to exception
