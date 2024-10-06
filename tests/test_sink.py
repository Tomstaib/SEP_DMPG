import unittest
from unittest.mock import Mock, patch
from simpy import Environment
from src.core.entity import Entity
from src.core.model import Model, ComponentType
from src.core.tally_statistic import TallyStatistic
from src.util.date_time import DateTime
import src.util.global_imports as gi
from src.core.sink import Sink
import logging


class TestSink(unittest.TestCase):
    def setUp(self):
        self.env = Mock(spec=Environment)
        self.env.now = 0  # Initialize env.now
        self.sink = Sink(self.env, "TestSink")

        # Define TRACE logging level
        if not hasattr(logging, 'TRACE'):
            logging.TRACE = 5  # Set TRACE to level 5 (lower than DEBUG)
            logging.addLevelName(logging.TRACE, "TRACE")

        # logging.getLogger().setLevel(logging.TRACE)

        # Add a custom trace method to the logging module
        def trace(self, message, *args, **kws):
            if self.isEnabledFor(logging.TRACE):
                self._log(logging.TRACE, message, args, **kws)

        logging.Logger.trace = trace

    def test_init(self):
        self.assertEqual(self.sink.name, "TestSink")
        self.assertEqual(self.sink.entities_processed, 0)
        self.assertEqual(self.sink.total_time_in_system, 0)
        self.assertEqual(self.sink.max_time_in_system_pivot_table, 0)
        self.assertEqual(self.sink.min_time_in_system_pivot_table, float('inf'))
        self.assertEqual(self.sink.number_entered_pivot_table, 0)
        self.assertIsInstance(self.sink.tally_statistic, TallyStatistic)
        self.assertIsNone(self.sink.addon_processing_done_method_with_parameters)
        self.assertEqual(self.sink.processed_entities, [])

    def test_reset(self):
        self.sink.entities_processed = 10
        self.sink.reset()
        self.assertEqual(self.sink.entities_processed, 0)

    @patch('src.util.global_imports.DURATION_WARM_UP', 10)
    def test_handle_entity_arrival_before_warmup(self):
        """Test handle_entity_arrival when env.now < DURATION_WARM_UP."""
        entity = Mock(spec=Entity)
        entity.creation_time = 0
        self.env.now = 5  # Less than warmup duration

        # Save initial values to check that they don't change
        initial_total_time_in_system = self.sink.total_time_in_system
        initial_max_time_in_system = self.sink.max_time_in_system_pivot_table
        initial_min_time_in_system = self.sink.min_time_in_system_pivot_table
        initial_number_entered = self.sink.number_entered_pivot_table

        # Process the entity
        self.sink.handle_entity_arrival(entity)

        # Assert that the values remain unchanged
        self.assertEqual(self.sink.total_time_in_system, initial_total_time_in_system)
        self.assertEqual(self.sink.max_time_in_system_pivot_table, initial_max_time_in_system)
        self.assertEqual(self.sink.min_time_in_system_pivot_table, initial_min_time_in_system)
        self.assertEqual(self.sink.number_entered_pivot_table, initial_number_entered)

    @patch('src.util.global_imports.DURATION_WARM_UP', 0)
    def test_handle_entity_arrival_during_warmup(self):
        entity = Mock(spec=Entity)
        entity.creation_time = 0
        self.env.now = 5
        self.sink.handle_entity_arrival(entity)
        self.assertEqual(self.sink.entities_processed, 1)
        self.assertEqual(self.sink.total_time_in_system, 5)
        self.assertEqual(self.sink.max_time_in_system_pivot_table, 5)
        self.assertEqual(self.sink.min_time_in_system_pivot_table, 5)
        self.assertEqual(self.sink.number_entered_pivot_table, 1)
        self.assertEqual(len(self.sink.processed_entities), 1)

    @patch('src.util.global_imports.DURATION_WARM_UP', 10)
    def test_handle_entity_arrival_after_warmup(self):
        entity = Mock(spec=Entity)
        entity.creation_time = 0
        self.env.now = 15
        self.sink.handle_entity_arrival(entity)
        self.assertEqual(self.sink.entities_processed, 1)
        self.assertEqual(self.sink.total_time_in_system, 15)
        self.assertEqual(self.sink.max_time_in_system_pivot_table, 15)
        self.assertEqual(self.sink.min_time_in_system_pivot_table, 15)
        self.assertEqual(self.sink.number_entered_pivot_table, 1)
        self.assertEqual(len(self.sink.processed_entities), 1)

    def test_handle_entity_arrival_with_addon_processing(self):
        addon_mock = Mock()
        self.sink.addon_processing_done_method_with_parameters = [addon_mock, "extra_param"]
        entity = Mock(spec=Entity)
        entity.creation_time = 0
        self.env.now = 5
        self.sink.handle_entity_arrival(entity)
        addon_mock.assert_called_once_with(self.sink, entity, "extra_param")

    def test_repr(self):
        self.assertEqual(repr(self.sink), "TestSink")

    @patch('src.core.model.Model.add_component')
    def test_model_component_registration(self, mock_add_component):
        sink = Sink(self.env, "NewSink")
        mock_add_component.assert_called_once_with(sink, ComponentType.SINKS)


if __name__ == '__main__':
    unittest.main()
