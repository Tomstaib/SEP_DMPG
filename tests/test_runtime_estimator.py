import sys
import os
import unittest
from unittest.mock import patch
import time

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Laufzeitprognose/src')
))

import util.runtime_estimator
from util.runtime_estimator import start_timer, end_timer, get_time_statistics, get_percentage_and_computing_times, print_stats


class TestRuntimeEstimator(unittest.TestCase):

    @patch('time.time', return_value=100.0)
    def test_start_timer(self, mock_time):
        """Test start_timer function"""
        start = start_timer()
        self.assertEqual(start, 100.0)
        mock_time.assert_called_once()

    @patch('time.time', return_value=105.0)
    def test_end_timer(self, mock_time):
        """Test end_timer function"""
        start = 100.0
        elapsed = end_timer(start)
        self.assertEqual(elapsed, 5.0)
        mock_time.assert_called_once()

    @patch('time.time', side_effect=[100.0, 105.0])
    def test_get_time_statistics(self, mock_time):
        """Test get_time_statistics function"""
        start = start_timer()
        elapsed = get_time_statistics(start)
        self.assertEqual(elapsed, 5.0)
        self.assertEqual(mock_time.call_count, 2)

    @patch('time.time', side_effect=[100.0, 105.0])
    def test_get_percentage_and_computing_times(self, mock_time):
        """Test get_percentage_and_computing_times function"""
        global seconds_previous_computations
        seconds_previous_computations = 0  # Initialisierung der globalen Variablen

        computing_time_start = start_timer()

        percentage, computed_time, time_to_complete, time_prediction, time_per_iteration = get_percentage_and_computing_times(
            computing_time_start, i=4, num_replications=10)

        self.assertEqual(percentage, " 50%")
        self.assertIn('0:00:05', computed_time)
        self.assertIn('0:00:05', time_to_complete)
        self.assertIn('0:00:10', time_prediction)
        self.assertIn('0:00:05', time_per_iteration)

    @patch('time.time', side_effect=[100.0, 105.0, 110.0, 115.0])
    def test_print_stats(self, mock_time):
        """Test print_stats function"""
        global seconds_previous_computations
        seconds_previous_computations = 0  # Initialisierung der globalen Variablen

        start = start_timer()

        with patch('builtins.print') as mock_print:
            print_stats(i=4, num_replications=10, start=start, tenth_percentage=1)
            print_stats(i=9, num_replications=10, start=start, tenth_percentage=1)

            self.assertEqual(mock_print.call_count, 4)


class TestRuntimeEstimatorEdgeCases(unittest.TestCase):

    @patch('time.time', return_value=105.0)
    def test_seconds_previous_computations_initialization(self, mock_time):
        """Test the initialization of seconds_previous_computations if it's not present."""
        if hasattr(util.runtime_estimator, 'seconds_previous_computations'):
            del util.runtime_estimator.seconds_previous_computations

        self.assertFalse(hasattr(util.runtime_estimator, 'seconds_previous_computations'))

        computing_time_start = 100.0

        percentage, computed_time, time_to_complete, time_prediction, time_per_iteration = get_percentage_and_computing_times(
            computing_time_start, i=4, num_replications=10)

        self.assertTrue(hasattr(util.runtime_estimator, 'seconds_previous_computations'))
        self.assertEqual(util.runtime_estimator.seconds_previous_computations, 5.0)

        self.assertEqual(percentage, " 50%")
        self.assertIn('0:00:05', computed_time)
        self.assertIn('0:00:05', time_to_complete)
        self.assertIn('0:00:10', time_prediction)
        self.assertIn('0:00:05', time_per_iteration)


if __name__ == '__main__':
    unittest.main()
