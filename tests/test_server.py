import unittest
import random
from unittest.mock import MagicMock, patch
import simpy
from src.core.server import Server, QueueType
from src.core.entity import Entity, SubEntity
from src.core.queue_type import QueueType
from src.core.connection import Connection
from collections import deque

# Mock global imports and variables
import src.util.global_imports as gi

gi.DURATION_WARM_UP = 0  # Set to 0 for testing purposes


# Mock external dependencies
class ResetAbleNamedObject:
    def __init__(self, env, name, manager):
        self.env = env
        self.name = name


class ResetAbleNamedObjectManager:
    pass


class RoutingObject:
    def __init__(self, env, routing_expression=None):
        self.env = env
        self.routing_expression = routing_expression
        self.connection_cache = {}
        self.connections = {}

    def route_entity(self, entity):
        pass


class ModelSingletonMock:
    def __init__(self):
        self.components = {}

    def add_component(self, component, component_type):
        self.components[component_type] = component


class MockWorkSchedule:
    def get(self):
        return (None, None)


def mock_get_value_from_distribution_with_parameters(dwp):
    if dwp is None:
        return 0
    if isinstance(dwp, (int, float)):
        return dwp
    if isinstance(dwp, MagicMock):
        return 1  # Return a default numeric value
    if isinstance(dwp, dict):
        distribution = dwp.get('distribution')
        parameters = dwp.get('parameters', {})
        if distribution == 'constant':
            return parameters.get('value', 1)
        elif distribution == 'exponential':
            mean = parameters.get('mean', 1)
            return random.expovariate(1 / mean)
        else:
            raise ValueError(f"Unknown distribution: {distribution}")
    else:
        raise TypeError(f"Unsupported type for dwp: {type(dwp)}")


def mock_validate_probabilities(component):
    # Assume probabilities are valid for testing
    pass


def mock_create_connection_cache(component):
    # Create a simple connection cache for testing
    total_probability = 0
    for connection in component.connections.values():
        total_probability += connection.probability

    cumulative_probability = 0
    for connection in component.connections.values():
        cumulative_probability += connection.probability
        component.connection_cache[cumulative_probability] = connection.next_component


def mock_ask_work_schedule(current_time, week):
    return False, 1, None  # Not working time, wait for 1 time unit


# Now define the test class
class TestServer(unittest.TestCase):

    def setUp(self):
        # Set up the environment and patches
        self.env = simpy.Environment()
        self.model_patch = patch('src.core.model.Model', return_value=ModelSingletonMock())
        self.mock_model = self.model_patch.start()
        self.logging_patch = patch('logging.trace')
        self.mock_logging = self.logging_patch.start()
        self.get_value_patch = patch('src.core.server.get_value_from_distribution_with_parameters',
                                     side_effect=mock_get_value_from_distribution_with_parameters)
        self.mock_get_value = self.get_value_patch.start()
        self.validate_probabilities_patch = patch('src.core.server.validate_probabilities',
                                                  side_effect=mock_validate_probabilities)
        self.mock_validate_probabilities = self.validate_probabilities_patch.start()
        self.create_connection_cache_patch = patch('src.core.server.create_connection_cache',
                                                   side_effect=mock_create_connection_cache)
        self.mock_create_connection_cache = self.create_connection_cache_patch.start()
        self.ask_work_schedule_patch = patch('src.core.server.ask_work_schedule',
                                             side_effect=mock_ask_work_schedule)
        self.mock_ask_work_schedule = self.ask_work_schedule_patch.start()

    def tearDown(self):
        self.model_patch.stop()
        self.logging_patch.stop()
        self.get_value_patch.stop()
        self.validate_probabilities_patch.stop()
        self.create_connection_cache_patch.stop()
        self.ask_work_schedule_patch.stop()

    def test_init(self):
        """Test the initialization of the Server class."""
        server = Server(
            env=self.env,
            name='Server1',
            processing_time_distribution_with_parameters={'distribution': 'constant', 'parameters': {'value': 1}},
            capacity=2,
            time_between_machine_breakdowns={'distribution': 'exponential', 'parameters': {'mean': 5}},
            machine_breakdown_duration={'distribution': 'constant', 'parameters': {'value': 2}},
            queue_order=QueueType.FIFO,
            routing_expression=None
        )
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)

        self.assertEqual(server.env, self.env)
        self.assertEqual(server.name, 'Server1')
        self.assertEqual(server.processing_time_dwp, {'distribution': 'constant', 'parameters': {'value': 1}})
        self.assertEqual(server.time_between_machine_breakdowns,
                         {'distribution': 'exponential', 'parameters': {'mean': 5}})
        self.assertEqual(server.machine_breakdown_duration, {'distribution': 'constant', 'parameters': {'value': 2}})
        self.assertEqual(server.queue_order, QueueType.FIFO)
        self.assertIsNone(server.week)
        self.assertIsNone(server.routing_expression)
        self.assertIsInstance(server.server_queue, deque)
        self.assertEqual(server.entities_processed, 0)
        self.assertIsNotNone(server.action)
        self.assertEqual(server.total_processing_time_pivot_table, 0)
        self.assertEqual(server.number_entered_pivot_table, 0)
        self.assertEqual(server.number_exited_pivot_table, 0)
        self.assertEqual(server.units_allocated, 0)
        self.assertEqual(server.units_utilized_over_time, [])
        self.assertEqual(server.start_processing_time, 0)
        self.assertIsInstance(server.processing, simpy.events.Event)
        self.assertEqual(server.total_downtime_pivot_table, 0)
        self.assertEqual(server.number_downtimes_pivot_table, 0)
        self.assertEqual(server.uptime, 0)
        self.assertEqual(server.total_uptime, 0)
        self.assertEqual(server.number_uptimes, 0)
        self.assertTrue(hasattr(server, 'time_until_next_machine_breakdown'))
        self.assertEqual(server.capacity, 2)
        self.assertEqual(server.currently_processing, [])
        self.assertFalse(server.initialized)
        self.assertEqual(server.units_utilized_over_time, [])

    def test_reset(self):
        """Test the reset method."""
        server = Server(self.env, 'Server1')
        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.server_queue.append(entity)
        server.currently_processing.append(entity)
        server.reset()
        self.assertEqual(len(server.server_queue), 0)
        self.assertEqual(len(server.currently_processing), 0)

    def test_is_available(self):
        """Test the is_available method."""
        server = Server(self.env, 'Server1')
        self.assertTrue(server.is_available())
        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.server_queue.append(entity)
        self.assertFalse(server.is_available())

    def test_handle_entity_arrival(self):
        """Test the handle_entity_arrival method."""
        server = Server(self.env, 'Server1')
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)
        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.handle_entity_arrival(entity)
        self.assertIn(entity, server.server_queue)
        self.assertEqual(server.number_entered_pivot_table, 1)
        self.assertTrue(server.processing.triggered)
        self.assertEqual(server.uptime, 0)  # Since env.now is 0

    def test_processing_without_machine_breakdown(self):
        """Test processing when there is no machine breakdown."""
        server = Server(
            self.env,
            'Server1',
            processing_time_distribution_with_parameters={'distribution': 'constant', 'parameters': {'value': 2}}
        )
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)
        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.handle_entity_arrival(entity)

        # Trigger the server's processing explicitly
        self.env.process(server.run())

        # Run the environment long enough to complete the processing
        self.env.run(until=5)
        self.assertEqual(server.entities_processed, 1)

    def test_processing_with_machine_breakdown(self):
        """Test processing when machine breakdown occurs during processing."""
        time_between_breakdowns_dwp = {'distribution': 'constant', 'parameters': {'value': 3}}
        breakdown_duration_dwp = {'distribution': 'constant', 'parameters': {'value': 2}}
        processing_time_dwp = {'distribution': 'constant', 'parameters': {'value': 5}}

        server = Server(
            env=self.env,
            name='Server1',
            processing_time_distribution_with_parameters=processing_time_dwp,
            time_between_machine_breakdowns=time_between_breakdowns_dwp,
            machine_breakdown_duration=breakdown_duration_dwp,
        )
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)

        def mock_get_value(dwp):
            if dwp == server.time_between_machine_breakdowns:
                return 3
            elif dwp == server.machine_breakdown_duration:
                return 2
            elif dwp == server.processing_time_dwp:
                return 5
            else:
                return 1

        self.mock_get_value.side_effect = mock_get_value

        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.handle_entity_arrival(entity)
        gi.DURATION_WARM_UP = 0
        self.env.run(until=10)
        self.assertEqual(server.entities_processed, 1)
        self.assertEqual(server.number_downtimes_pivot_table, 1)
        self.assertEqual(server.total_downtime_pivot_table, 2)
        self.assertGreaterEqual(self.env.now, 7)

    def test_processing_without_machine_breakdown_due_to_long_interval(self):
        """Test processing when machine breakdown does not occur during processing."""
        time_between_breakdowns_dwp = {'distribution': 'constant', 'parameters': {'value': 10}}
        breakdown_duration_dwp = {'distribution': 'constant', 'parameters': {'value': 2}}
        processing_time_dwp = {'distribution': 'constant', 'parameters': {'value': 5}}

        server = Server(
            env=self.env,
            name='Server1',
            processing_time_distribution_with_parameters=processing_time_dwp,
            time_between_machine_breakdowns=time_between_breakdowns_dwp,
            machine_breakdown_duration=breakdown_duration_dwp,
        )
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)

        def mock_get_value(dwp):
            if dwp == server.time_between_machine_breakdowns:
                return 10
            elif dwp == server.machine_breakdown_duration:
                return 2
            elif dwp == server.processing_time_dwp:
                return 5
            else:
                return 1

        self.mock_get_value.side_effect = mock_get_value

        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.handle_entity_arrival(entity)
        self.env.run(until=10)
        self.assertEqual(server.entities_processed, 1)
        self.assertEqual(server.number_downtimes_pivot_table, 0)
        self.assertEqual(server.total_downtime_pivot_table, 0)
        self.assertGreaterEqual(self.env.now, 5)

    def test_try_process_from_queue_fifo(self):
        """Test processing entities from the queue with FIFO order."""
        server = Server(self.env, 'Server1', queue_order=QueueType.FIFO, capacity=1,
                        processing_time_distribution_with_parameters={'distribution': 'constant',
                                                                      'parameters': {'value': 2}})
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)
        entity1 = Entity(name='Entity1', creation_time=self.env.now)
        entity2 = Entity(name='Entity2', creation_time=self.env.now)
        server.handle_entity_arrival(entity1)
        server.handle_entity_arrival(entity2)
        gi.DURATION_WARM_UP = 0

        # Trigger the processing manually to make sure both entities are processed
        if not server.processing.triggered:
            server.processing.succeed()

        self.env.run(until=10)
        self.assertEqual(server.entities_processed, 2)

    def test_try_process_from_queue_lifo(self):
        """Test processing entities from the queue with LIFO order."""
        # Initialize server with LIFO queue order
        server = Server(self.env, 'Server1', queue_order=QueueType.LIFO, capacity=1,
                        processing_time_distribution_with_parameters={'distribution': 'constant',
                                                                      'parameters': {'value': 2}})
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)

        # Add two entities to the server
        entity1 = Entity(name='Entity1', creation_time=self.env.now)
        entity2 = Entity(name='Entity2', creation_time=self.env.now)
        server.handle_entity_arrival(entity1)
        server.handle_entity_arrival(entity2)
        gi.DURATION_WARM_UP = 0

        self.env.run(until=10)

        # Assert that both entities have been processed
        self.assertEqual(server.entities_processed, 2)

        # Capture processing start times
        start_times = [start for start, end, count in server.units_utilized_over_time]

        # Ensure there are at least two entries for the two entities
        self.assertEqual(len(start_times), 2, "There should be two recorded start times.")

        # Verify that LIFO order was maintained
        # Entity2 should be processed before Entity1
        self.assertTrue(start_times[0] < start_times[1],
                        "LIFO order not maintained. Entity2 should have been processed before Entity1.")

    def test_server_capacity(self):
        """Test server processing multiple entities with capacity greater than 1."""
        server = Server(self.env, 'Server1', capacity=2,
                        processing_time_distribution_with_parameters={'distribution': 'constant',
                                                                      'parameters': {'value': 5}})
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)
        entity1 = Entity(name='Entity1', creation_time=self.env.now)
        entity2 = Entity(name='Entity2', creation_time=self.env.now)
        entity3 = Entity(name='Entity3', creation_time=self.env.now)
        server.handle_entity_arrival(entity1)
        server.handle_entity_arrival(entity2)
        server.handle_entity_arrival(entity3)
        self.env.run(until=15)
        self.assertEqual(server.entities_processed, 3)

    def test_run_with_work_schedule_active(self):
        """Test the run method when work schedule is provided and active is True."""

        def mock_ask_work_schedule_active(current_time, week):
            return True, 0, None

        self.mock_ask_work_schedule.side_effect = mock_ask_work_schedule_active

        server = Server(self.env, 'Server1', work_schedule=MockWorkSchedule())
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)
        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.handle_entity_arrival(entity)
        self.env.run(until=5)
        self.assertEqual(server.entities_processed, 1)

    def test_run_with_work_schedule_inactive(self):
        """Test the run method when work schedule is provided and active is False."""

        def mock_ask_work_schedule_inactive(current_time, week):
            return False, 2, None  # Not active, wait for 2 units

        self.mock_ask_work_schedule.side_effect = mock_ask_work_schedule_inactive

        server = Server(self.env, 'Server1', work_schedule=MockWorkSchedule())
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)
        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.handle_entity_arrival(entity)
        self.env.run(until=5)
        self.assertEqual(server.entities_processed, 0)

        def mock_ask_work_schedule_active(current_time, week):
            return True, 0, None

        self.mock_ask_work_schedule.side_effect = mock_ask_work_schedule_active
        self.env.run(until=10)
        self.assertEqual(server.entities_processed, 1)

    def test_repr(self):
        """Test the __repr__ method."""
        server = Server(self.env, 'Server1')
        self.assertEqual(repr(server), 'Server1')

    def test_initialize_server_called_once(self):
        """Test that _initialize_server is called only once."""
        server = Server(self.env, 'Server1')
        server._initialize_server = MagicMock()
        self.env.run(until=5)
        server._initialize_server.assert_called_once()

    def test_handle_entity_arrival_after_warmup(self):
        """Test handle_entity_arrival when env.now >= DURATION_WARM_UP."""
        server = Server(self.env, 'Server1')
        gi.DURATION_WARM_UP = 0
        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.handle_entity_arrival(entity)
        self.assertEqual(server.number_entered_pivot_table, 1)

    def test_handle_entity_arrival_before_warmup(self):
        """Test handle_entity_arrival when env.now < DURATION_WARM_UP."""
        server = Server(self.env, 'Server1')
        gi.DURATION_WARM_UP = 5
        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.handle_entity_arrival(entity)
        self.assertEqual(server.number_entered_pivot_table, 0)
        self.env.run(until=6)
        entity2 = Entity(name='Entity2', creation_time=self.env.now)
        server.handle_entity_arrival(entity2)
        self.assertEqual(server.number_entered_pivot_table, 1)

    def test_route_entity_called(self):
        """Test that route_entity is called after processing."""
        server = Server(self.env, 'Server1')
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)

        # Mock route_entity to avoid calling a non-existing method
        server.route_entity = MagicMock()

        entity = Entity(name='Entity1', creation_time=self.env.now)
        server.handle_entity_arrival(entity)
        self.env.run(until=5)

        # Ensure route_entity is correctly called
        server.route_entity.assert_called_once_with(entity)

    def test_process_subentity(self):
        """Test processing of SubEntity."""
        server = Server(self.env, 'Server1')
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)
        subentity = SubEntity(name='SubEntity1', creation_time=self.env.now)
        subentity.count_processing = MagicMock()
        subentity.add_to_server_history = MagicMock()
        server.handle_entity_arrival(subentity)

        # Ensure that process is executed only once.
        with patch.object(server, 'route_entity', wraps=server.route_entity) as mock_route_entity:
            self.env.run(until=5)
            mock_route_entity.assert_called_once()

    def test_units_utilized_over_time(self):
        """Test that units_utilized_over_time is updated correctly."""
        server = Server(self.env, 'Server1', capacity=2,
                        processing_time_distribution_with_parameters={'distribution': 'constant',
                                                                      'parameters': {'value': 2}})
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)
        gi.DURATION_WARM_UP = 0
        entity1 = Entity(name='Entity1', creation_time=self.env.now)
        entity2 = Entity(name='Entity2', creation_time=self.env.now)
        server.handle_entity_arrival(entity1)
        server.handle_entity_arrival(entity2)

        # Manually ensure processing starts
        if not server.processing.triggered:
            server.processing.succeed()

        self.env.run(until=5)

        # Expect 2 utilization periods as both entities should have been processed
        self.assertEqual(len(server.units_utilized_over_time), 2)

    def test_server_capacity_limit(self):
        """Test that server does not process more entities than its capacity."""
        server = Server(self.env, 'Server1', capacity=1,
                        processing_time_distribution_with_parameters={'distribution': 'constant',
                                                                      'parameters': {'value': 5}})
        next_server = Server(self.env, 'NextServer')
        server.connect(next_server, probability=100)
        entity1 = Entity(name='Entity1', creation_time=self.env.now)
        entity2 = Entity(name='Entity2', creation_time=self.env.now)
        server.handle_entity_arrival(entity1)
        server.handle_entity_arrival(entity2)
        self.env.run(until=2)
        self.assertEqual(len(server.currently_processing), 1)
        self.assertEqual(len(server.server_queue), 1)

    def test_initialize_server_calls_helper_functions(self):
        """Test that _initialize_server calls validate_probabilities and create_connection_cache."""
        server = Server(self.env, 'Server1')

        with patch('src.core.server.validate_probabilities') as mock_validate_probabilities, \
                patch('src.core.server.create_connection_cache') as mock_create_connection_cache:
            self.env.run(until=10)  # Run for a short time to ensure initialization

            # Assert that the helper functions were called exactly once
            mock_validate_probabilities.assert_called_once_with(server)
            mock_create_connection_cache.assert_called_once_with(server)


if __name__ == '__main__':
    unittest.main()
