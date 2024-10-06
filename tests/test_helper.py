import unittest
from unittest.mock import mock_open, patch, Mock
import json
import logging
from src.util.helper import load_config, get_value_from_distribution_with_parameters, validate_probabilities, \
    create_connection_cache, add_logging_level, round_value, ROUND_DECIMAL_PLACES


# 1. Test class for load_config function
class TestLoadConfig(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    def test_load_valid_config(self, mock_file):
        result = load_config('dummy_path')
        self.assertEqual(result, {"key": "value"})

    @patch("builtins.open", new_callable=mock_open, read_data='invalid_json')
    def test_load_invalid_json(self, mock_file):
        with self.assertRaises(json.JSONDecodeError):
            load_config('dummy_path')

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_non_existent_file(self, mock_file):
        with self.assertRaises(FileNotFoundError):
            load_config('dummy_path')


# 2. Test class for get_value_from_distribution_with_parameters function
class TestGetValueFromDistributionWithParameters(unittest.TestCase):

    def test_distribution_with_parameters(self):
        mock_distribution = Mock(return_value=5.0)
        result = get_value_from_distribution_with_parameters((mock_distribution, 1, 10))
        mock_distribution.assert_called_once_with(1, 10)
        self.assertEqual(result, 5.0)

    def test_distribution_without_parameters(self):
        mock_distribution = Mock(return_value=42.0)
        result = get_value_from_distribution_with_parameters((mock_distribution,))
        mock_distribution.assert_called_once_with()
        self.assertEqual(result, 42.0)


# 3. Test class for validate_probabilities function
class TestValidateProbabilities(unittest.TestCase):

    def test_valid_probabilities(self):
        component = MockComponent('component1', {
            'conn1': MockConnection(40),
            'conn2': MockConnection(60)
        })
        validate_probabilities(component)  # Should pass without exception

    def test_validate_probabilities_exceeds_100(self):
        component = MockComponent('component_exceed', {
            'conn1': MockConnection(60),
            'conn2': MockConnection(50)
        })
        with self.assertRaises(ValueError) as context:
            validate_probabilities(component)
        self.assertEqual(str(context.exception), "Total probability exceeds 100% for source component_exceed")

    def test_unspecified_probabilities(self):
        component = MockComponent('component3', {
            'conn1': MockConnection(50),
            'conn2': MockConnection(None)
        })
        validate_probabilities(component)
        self.assertEqual(component.connections['conn2'].probability, 50)

    def test_validate_probabilities_does_not_sum_to_100(self):
        component = MockComponent('component_invalid', {
            'conn1': MockConnection(40),
            'conn2': MockConnection(30)
        })
        with self.assertRaises(ValueError) as context:
            validate_probabilities(component)
        self.assertEqual(str(context.exception), "Total probability 70.000 does not sum up to 100% for source component_invalid")

    def test_validate_probabilities_incomplete_adjustment(self):
        component = MockComponent('component_partial', {
            'conn1': MockConnection(60),  # Fixed value
            'conn2': MockConnection(None),  # Should fill remaining probability
            'conn3': MockConnection(50)  # Causes the total to exceed 100
        })
        with self.assertRaises(ValueError) as context:
            validate_probabilities(component)

        # Expect the error message indicating total probability exceeds 100%
        self.assertEqual(str(context.exception), "Total probability exceeds 100% for source component_partial")


# 4. Test class for create_connection_cache function
class TestCreateConnectionCache(unittest.TestCase):

    def test_create_connection_cache(self):
        component = MockComponent('component', {
            'conn1': MockConnection(40),
            'conn2': MockConnection(60)
        })
        component.connection_cache = {}
        create_connection_cache(component)
        self.assertEqual(len(component.connection_cache), 2)
        self.assertIn(40, component.connection_cache)
        self.assertIn(100, component.connection_cache)

    def test_create_connection_cache_no_connections(self):
        component = MockComponent('empty_component', {})
        create_connection_cache(component)
        self.assertEqual(len(component.connection_cache), 0)

    def test_create_connection_cache_single_connection(self):
        component = MockComponent('component_single', {
            'conn1': MockConnection(100)
        })
        create_connection_cache(component)
        self.assertIn(100, component.connection_cache)
        self.assertEqual(len(component.connection_cache), 1)

    def test_create_connection_cache_with_incomplete_probabilities(self):
        component = MockComponent('component_partial', {
            'conn1': MockConnection(40),
            'conn2': MockConnection(60)
        })
        component.connection_cache = {}
        create_connection_cache(component)
        self.assertIn(40, component.connection_cache)
        self.assertIn(100, component.connection_cache)
        self.assertEqual(len(component.connection_cache), 2)


# 5. Test class for add_logging_level function
class TestAddLoggingLevel(unittest.TestCase):

    def tearDown(self):
        # Clear logging state after test to avoid conflicts
        logging.root.manager.loggerDict.clear()

    def test_add_logging_level(self):
        add_logging_level('CUSTOM', 25)
        self.assertEqual(logging.CUSTOM, 25)
        self.assertTrue(hasattr(logging, 'custom'))

    def test_add_logging_level_existing(self):
        add_logging_level('TEST_LEVEL', 35)
        self.assertEqual(logging.TEST_LEVEL, 35)
        with self.assertRaises(AttributeError):
            add_logging_level('TEST_LEVEL', 35)

    def test_add_logging_level_method_name_conflict(self):
        with self.assertRaises(AttributeError):
            add_logging_level('DEBUG', 25)

    def test_add_logging_level_method_name_exists_in_logging_module(self):
        with self.assertRaises(AttributeError):
            add_logging_level('EXISTING_LEVEL', 35, method_name='debug')  # 'debug' already exists in logging module

    def test_add_logging_level_method_name_exists_in_logger_class(self):
        # Dynamically add a custom method to the Logger class
        setattr(logging.getLoggerClass(), 'custom_method', lambda self, msg: None)

        try:
            with self.assertRaises(AttributeError) as context:
                add_logging_level('CUSTOM_LEVEL', 35,
                                  method_name='custom_method')

            self.assertEqual(str(context.exception), "custom_method already defined in logger class")

        finally:
            delattr(logging.getLoggerClass(), 'custom_method')

    def test_log_for_new_custom_level(self):
        add_logging_level('CUSTOM_LOG', 35)

        logger = logging.getLogger('test_logger')
        with patch.object(logger, '_log') as mock_log:
            logger.custom_log('This is a custom log message')

            # Check if the logger's _log method was called with the new level
            mock_log.assert_called_once()
            mock_log.assert_called_with(35, 'This is a custom log message', ())

    def test_log_for_custom_level_enabled(self):
        add_logging_level('CUSTOM_LOG_ENABLED', 35)

        logger = logging.getLogger('test_logger')
        logger.setLevel(35)

        with patch.object(logger, '_log') as mock_log:
            logger.custom_log_enabled('This is a custom log message when enabled')

            mock_log.assert_called_once_with(35, 'This is a custom log message when enabled', ())

    def test_log_for_custom_level_disabled(self):
        add_logging_level('CUSTOM_LOG_DISABLED', 35)

        logger = logging.getLogger('test_logger')
        logger.setLevel(40)

        with patch.object(logger, '_log') as mock_log:
            logger.custom_log_disabled('This log message should not appear')

            mock_log.assert_not_called()

    def test_log_to_root_for_custom_level(self):
        add_logging_level('ROOT_CUSTOM_LOG', 35)

        with patch('logging.log') as mock_log:
            logging.root_custom_log('Root logger custom message')

            # Verify that the root logger is logging at the custom level
            mock_log.assert_called_once_with(35, 'Root logger custom message')


# 6. Test class for round_value function
class TestRoundValue(unittest.TestCase):

    def test_round_float(self):
        self.assertEqual(round_value(3.14159265), 3.1416)

    def test_round_int(self):
        self.assertEqual(round_value(42), 42)


# Mock classes for component testing
class MockConnection:
    def __init__(self, probability=None):
        self.probability = probability


class MockComponent:
    def __init__(self, name, connections):
        self.name = name
        self.connections = connections
        self.connection_cache = {}


if __name__ == "__main__":
    unittest.main()
