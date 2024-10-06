import unittest
import logging
import pandas as pd
import random
from unittest.mock import patch
from src.util.global_imports import RANDOM_SEED, DURATION_WARM_UP, Stats, set_duration_warm_up, DAYS_PER_WEEK, \
    HOURS_PER_DAY, MINUTES_PER_HOUR, SECONDS_PER_MINUTE
import src.util.global_imports as gi


class TestGlobalImports(unittest.TestCase):

    def setUp(self):
        set_duration_warm_up(0)

    def test_global_constants(self):
        """Test that global constants are correctly initialized."""
        self.assertEqual(RANDOM_SEED, 1)
        self.assertEqual(DAYS_PER_WEEK, 7)
        self.assertEqual(HOURS_PER_DAY, 24)
        self.assertEqual(MINUTES_PER_HOUR, 60)
        self.assertEqual(SECONDS_PER_MINUTE, 60)

    def test_random_seed(self):
        """Test that the random seed is set correctly."""
        random.seed(RANDOM_SEED)
        # Ensure that the first random number generated is consistent
        self.assertEqual(random.randint(1, 100), 18)

    @patch('logging.Logger.trace')
    def test_logging_configuration(self, mock_trace):
        """Test the logging configuration, including the custom TRACE level."""
        # Custom TRACE level is defined as DEBUG + 5, which should fall between DEBUG and INFO
        logging.getLogger().trace('This is a TRACE level log')
        mock_trace.assert_called_once_with('This is a TRACE level log')

    def test_pandas_configuration(self):
        """Test that pandas configuration options are correctly set."""
        self.assertEqual(pd.get_option('display.max_columns'), None)
        self.assertEqual(pd.get_option('display.max_colwidth'), None)
        self.assertEqual(pd.get_option('max_seq_item'), None)
        self.assertEqual(pd.get_option('display.width'), 1000)

    def test_stats_singleton(self):
        """Test that the Stats class behaves as a singleton."""
        Stats.all_detailed_stats = []
        stats_instance_1 = Stats()  # Ensure singleton is retrieved correctly
        stats_instance_1.all_detailed_stats.append('Run1')

        stats_instance_2 = Stats()  # Retrieve the same singleton instance
        self.assertEqual(stats_instance_2.all_detailed_stats, ['Run1'])
        self.assertIs(stats_instance_1, stats_instance_2)

    def test_set_duration_warm_up(self):
        """Test that set_duration_warm_up correctly sets the global DURATION_WARM_UP."""
        self.assertEqual(gi.DURATION_WARM_UP, 0)
        set_duration_warm_up(100)
        self.assertEqual(gi.DURATION_WARM_UP, 100)


if __name__ == '__main__':
    unittest.main()
