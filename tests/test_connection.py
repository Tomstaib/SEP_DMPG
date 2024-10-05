import unittest
import simpy
from unittest.mock import MagicMock
import logging
from collections import deque
from src.core.connection import Connection


class Entity:
    def __init__(self, name):
        self.name = name


class ResetAbleNamedObject:
    def __init__(self, env, name, manager):
        self.env = env
        self.name = name


class ResetAbleNamedObjectManager:
    def __init__(self):
        self.objects = []


class RoutingObject:
    def __init__(self, env):
        self.env = env


class DateTime:
    @staticmethod
    def get(time):
        return f"Time: {time}"


# Mock ENTITY_PROCESSING_LOG_ENTRY
ENTITY_PROCESSING_LOG_ENTRY = "{} at {}"


# Mock global_imports
class gi:
    DURATION_WARM_UP = 0


class TestConnection(unittest.TestCase):
    def setUp(self):
        # Set up the simulation environment
        self.env = simpy.Environment()
        # Mock the origin and next components
        self.origin_component = MagicMock()
        self.origin_component.name = "OriginComponent"
        self.origin_component.env = self.env
        self.origin_component.number_exited = 0

        self.next_component = MagicMock()
        self.next_component.name = "NextComponent"
        self.next_component.process_entity = MagicMock()
        self.next_component.env = self.env

        # Mock the Entity class
        self.entity = Entity("TestEntity")

        logging.basicConfig(level=logging.TRACE)

    def test_init_with_all_parameters(self):
        connection = Connection(
            env=self.env,
            origin_component=self.origin_component,
            next_component=self.next_component,
            name="TestConnection",
            process_duration=5,
            probability=0.5
        )
        self.assertEqual(connection.env, self.env)
        self.assertEqual(connection.origin_component, self.origin_component)
        self.assertEqual(connection.next_component, self.next_component)
        self.assertEqual(connection.name, "TestConnection")
        self.assertEqual(connection.process_duration, 5)
        self.assertEqual(connection.probability, 0.5)
        self.assertEqual(connection.entities_processed, 0)
        self.assertEqual(connection.number_entered, 0)
        self.assertIsInstance(connection.entities_queue, deque)
        self.assertFalse(connection.processing.triggered)
        self.assertIsNotNone(connection.action)  # The process action

    def test_init_with_minimum_parameters(self):
        connection = Connection(
            env=self.env,
            origin_component=self.origin_component,
            next_component=self.next_component,
            name="TestConnection"
        )
        self.assertIsNone(connection.process_duration)
        self.assertIsNone(connection.probability)

    def test_reset(self):
        connection = Connection(
            env=self.env,
            origin_component=self.origin_component,
            next_component=self.next_component,
            name="TestConnection"
        )
        # Simulate processing
        connection.entities_processed = 5
        connection.entities_queue.append(self.entity)

        connection.reset()
        self.assertEqual(connection.entities_processed, 0)
        self.assertEqual(len(connection.entities_queue), 0)

    def test_process_entity_when_not_processing(self):
        connection = Connection(
            env=self.env,
            origin_component=self.origin_component,
            next_component=self.next_component,
            name="TestConnection"
        )
        # processing event is not triggered
        self.assertFalse(connection.processing.triggered)
        connection.handle_entity_arrival(self.entity)
        self.assertIn(self.entity, connection.entities_queue)
        self.assertTrue(connection.processing.triggered)

    def test_process_entity_when_already_processing(self):
        connection = Connection(
            env=self.env,
            origin_component=self.origin_component,
            next_component=self.next_component,
            name="TestConnection"
        )
        # Manually trigger processing
        connection.processing.succeed()
        self.assertTrue(connection.processing.triggered)
        connection.handle_entity_arrival(self.entity)
        self.assertIn(self.entity, connection.entities_queue)
        # processing should remain triggered
        self.assertTrue(connection.processing.triggered)

    def test_run_with_process_duration(self):
        connection = Connection(
            env=self.env,
            origin_component=self.origin_component,
            next_component=self.next_component,
            name="TestConnection",
            process_duration=2
        )
        # Add entities to the connection
        connection.handle_entity_arrival(self.entity)
        # Run the environment
        self.env.run()
        # Verify that entity was processed after process_duration
        self.assertEqual(connection.entities_processed, 1)
        self.assertEqual(connection.number_entered, 1)
        self.assertEqual(self.origin_component.number_exited, 1)
        self.next_component.handle_entity_arrival.assert_called_with(self.entity)
        self.assertEqual(self.env.now, 2)

    def test_run_without_process_duration(self):
        connection = Connection(
            env=self.env,
            origin_component=self.origin_component,
            next_component=self.next_component,
            name="TestConnection"
        )
        # Add entities to the connection
        connection.handle_entity_arrival(self.entity)
        # Run the environment
        self.env.run()
        # Verify that entity was processed immediately
        self.assertEqual(connection.entities_processed, 1)
        self.assertEqual(connection.number_entered, 1)
        self.assertEqual(self.origin_component.number_exited, 1)
        self.next_component.handle_entity_arrival.assert_called_with(self.entity)
        self.assertEqual(self.env.now, 0)  # No time should have passed

    def test_run_with_empty_queue(self):
        connection = Connection(
            env=self.env,
            origin_component=self.origin_component,
            next_component=self.next_component,
            name="TestConnection"
        )
        # Run the environment briefly
        self.env.run(until=1)
        # Since no entities were added, nothing should happen
        self.assertEqual(connection.entities_processed, 0)
        self.assertEqual(connection.number_entered, 0)
        self.next_component.handle_entity_arrival.assert_not_called()

    def test_repr(self):
        connection = Connection(
            env=self.env,
            origin_component=self.origin_component,
            next_component=self.next_component,
            name="TestConnection"
        )
        self.assertEqual(repr(connection), "TestConnection")


if __name__ == '__main__':
    unittest.main()
