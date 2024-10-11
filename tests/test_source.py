import unittest
import simpy
from unittest.mock import patch
import logging
import pandas as pd
from io import StringIO
from src.core.source import Source


# Mocking external dependencies
def get_value_from_distribution_with_parameters(dist_with_params):
    # For testing purposes, return a fixed value
    return 1


def validate_probabilities(self):
    """For testing purposes"""
    pass


def create_connection_cache(self):
    """For testing purposes"""
    pass


class Entity:
    def __init__(self, name, creation_time):
        self.name = name
        self.creation_time = creation_time


class DateTime:
    @staticmethod
    def get(time):
        return f"Time: {time}"


class gi:
    DURATION_WARM_UP = 0


class Model:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Model, cls).__new__(cls)
            cls._instance.components = []
        return cls._instance

    def add_component(self, component, component_type):
        self.components.append((component, component_type))


class ComponentType:
    SOURCES = 'sources'


class TestSource(unittest.TestCase):
    def setUp(self):
        # Patching the external dependencies
        patcher1 = patch('src.core.source.get_value_from_distribution_with_parameters',
                         get_value_from_distribution_with_parameters)
        patcher2 = patch('src.core.source.validate_probabilities', validate_probabilities)
        patcher3 = patch('src.core.source.create_connection_cache', create_connection_cache)
        patcher4 = patch('src.core.source.Entity', Entity)
        patcher5 = patch('src.core.source.DateTime', DateTime)
        patcher6 = patch('src.util.global_imports', gi)
        patcher7 = patch('src.core.source.Model', Model)
        patcher8 = patch('src.core.source.ComponentType', ComponentType)
        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)
        self.addCleanup(patcher3.stop)
        self.addCleanup(patcher4.stop)
        self.addCleanup(patcher5.stop)
        self.addCleanup(patcher6.stop)
        self.addCleanup(patcher7.stop)
        self.addCleanup(patcher8.stop)
        patcher1.start()
        patcher2.start()
        patcher3.start()
        patcher4.start()
        patcher5.start()
        patcher6.start()
        patcher7.start()
        patcher8.start()

    def test_source_creation_with_distribution(self):
        env = simpy.Environment()
        creation_time_dwp = (lambda: 1, {})
        source = Source(env, 'TestSource', creation_time_distribution_with_parameters=creation_time_dwp)
        env.run(until=5.0001)  # run time slightly above expected
        self.assertEqual(len(source.entities), 5)
        self.assertEqual(source.entities_created_pivot_table, 5)

    def test_source_creation_with_arrival_table(self):
        csv_data = StringIO("""arrival_time
    1
    2
    3
    4
    5
    """)
        arrival_table = pd.read_csv(csv_data)
        with patch('pandas.read_csv', return_value=arrival_table):
            env = simpy.Environment()
            source = Source(env, 'TestSource', arrival_table_path='dummy_path')
            env.run(until=6)
            self.assertEqual(len(source.entities), 5)
            self.assertEqual(source.entities_created_pivot_table, 5)

    def test_reset(self):
        """Test the reset method."""
        env = simpy.Environment()
        source = Source(env, 'TestSource', creation_time_distribution_with_parameters=(lambda: 1, {}))
        env.run(until=5)
        source.reset()
        self.assertEqual(source.entities_created_pivot_table, 0)
        self.assertEqual(len(source.entities), 0)
        self.assertEqual(source.number_exited_pivot_table, 0)
        self.assertEqual(source.next_components, [])

    def test_arrival_table_based_wait_time(self):
        """Test arrival_table_based_wait_time method."""
        csv_data = StringIO("""arrival_time
    1
    3
    6
    10
    15
    """)
        arrival_table = pd.read_csv(csv_data)
        with patch('pandas.read_csv', return_value=arrival_table):
            env = simpy.Environment()
            source = Source(env, 'TestSource', arrival_table_path='dummy_path')
            wait_time = source.arrival_table_based_wait_time()
            self.assertEqual(wait_time, 1 - env.now)
            self.assertEqual(source.arrival_table_index, 1)

    def test_repr(self):
        """Test the __repr__ method."""
        env = simpy.Environment()
        source = Source(env, 'TestSource')
        self.assertEqual(repr(source), 'TestSource')

    def test_arrival_table_exhausted(self):
        """Test behavior when arrival_table runs out of entries."""
        csv_data = StringIO("""arrival_time
    1
    2
    3
    """)
        arrival_table = pd.read_csv(csv_data)
        with patch('pandas.read_csv', return_value=arrival_table):
            env = simpy.Environment()
            source = Source(env, 'TestSource', arrival_table_path='dummy_path')
            env.run()
            self.assertEqual(len(source.entities), 3)
            self.assertEqual(source.entities_created_pivot_table, 3)

    def test_negative_wait_time(self):
        """Test behavior when wait_time is negative."""
        csv_data = StringIO("""arrival_time
    -1
    0
    """)
        arrival_table = pd.read_csv(csv_data)
        with patch('pandas.read_csv', return_value=arrival_table):
            env = simpy.Environment()
            source = Source(env, 'TestSource', arrival_table_path='dummy_path')
            with self.assertRaises(ValueError):
                env.run(until=1)

    def test_warm_up_period(self):
        """Test behavior during warm-up period."""
        with patch('src.core.source.gi.DURATION_WARM_UP', 5):
            env = simpy.Environment()
            creation_time_dwp = (lambda: 1, {})
            source = Source(env, 'TestSource', creation_time_distribution_with_parameters=creation_time_dwp)
            env.run(until=4.001)
            self.assertEqual(len(source.entities), 4)
            self.assertEqual(source.entities_created_pivot_table, 0)  # no entities created
            env.run(until=6.001)
            self.assertEqual(len(source.entities), 6)
            self.assertEqual(source.entities_created_pivot_table, 2)  # 2 entities created since 4


if __name__ == '__main__':
    unittest.main()
