import unittest
from datetime import datetime
from src.util.date_time import DateTime, TimeComponent


class TestDateTime(unittest.TestCase):

    def setUp(self):
        # Ensure locale is set to "de_DE" as per the main script for consistent date formatting
        DateTime.set(datetime(2024, 12, 12, 0, 0, 0))

    def test_set_method(self):
        """Test the set method to ensure the initial date and time are set correctly."""
        new_date_time = datetime(2023, 1, 1, 12, 0, 0)
        DateTime.set(new_date_time)
        self.assertEqual(DateTime.initial_date_time, new_date_time)

    def test_get_method_default_mapping(self):
        """Test the get method with default simpy_time_mapped_to (minutes) and time_string_from_initial_date=True."""
        DateTime.map(TimeComponent.minute)
        result = DateTime.get(10)  # 10 minutes after the initial date
        self.assertIn("10", result)  # Ensure delta includes 10 minutes
        self.assertIn("Thu 12 Dec 2024", result)  # Ensure date formatting includes initial date

    def test_get_method_without_initial_date_string(self):
        """Test the get method with time_string_from_initial_date=False."""
        DateTime.map(TimeComponent.minute)
        result = DateTime.get(10, time_string_from_initial_date=False)
        self.assertEqual(result, "0:10:00")  # Only the delta in time should be returned

    def test_get_method_with_weekday_hour_minute(self):
        """Test the get method with get_weekday_hour_minute=True to ensure correct weekday, hour, and minute."""
        DateTime.map(TimeComponent.hour)
        weekday, hour, minute = DateTime.get(25.32, time_string_from_initial_date=False, get_weekday_hour_minute=True)
        self.assertEqual(weekday, 5)  # Thursday (12 Dec 2024) + 1 day = Friday (weekday 5)
        self.assertEqual(hour, 1)  # 25.32 hours from midnight = 01:00 (1 AM)
        self.assertEqual(minute, 19)  # 0.32 hours = 19 minutes

    def test_get_method_mapped_to_seconds(self):
        """Test the get method with simpy_time_mapped_to set to seconds."""
        DateTime.map(TimeComponent.second)
        result = DateTime.get(0.01)  # 0.01 seconds after the initial date
        self.assertIn("0.01", result)  # Ensure delta includes 0.01 seconds
        self.assertIn("Thu 12 Dec 2024", result)  # Ensure date formatting includes initial date

    def test_get_method_mapped_to_hours(self):
        """Test the get method with simpy_time_mapped_to set to hours."""
        DateTime.map(TimeComponent.hour)
        result = DateTime.get(25.32)  # 25.32 hours after the initial date
        self.assertIn("1 day", result)  # Ensure 1 day is included in the delta
        self.assertIn("Fri 13 Dec 2024", result)  # Ensure correct date

    def test_map_method(self):
        """Test the map method to ensure correct mapping to TimeComponent."""
        DateTime.map(TimeComponent.second)
        self.assertEqual(DateTime.simpy_time_mapped_to, TimeComponent.second)

        DateTime.map(TimeComponent.minute)
        self.assertEqual(DateTime.simpy_time_mapped_to, TimeComponent.minute)

        DateTime.map(TimeComponent.hour)
        self.assertEqual(DateTime.simpy_time_mapped_to, TimeComponent.hour)

    def test_map_time_to_steps(self):
        """Test the map_time_to_steps method for correct step calculation."""
        DateTime.map(TimeComponent.second)
        steps = DateTime.map_time_to_steps(day=1, hour=1, minute=1, second=1)
        self.assertAlmostEqual(steps, 90061)  # 1 day + 1 hour + 1 minute + 1 second in seconds

        DateTime.map(TimeComponent.minute)
        steps = DateTime.map_time_to_steps(day=1, hour=1, minute=1)
        self.assertAlmostEqual(steps, 1501)  # 1 day + 1 hour + 1 minute in minutes

        DateTime.map(TimeComponent.hour)
        steps = DateTime.map_time_to_steps(day=1, hour=1)
        self.assertAlmostEqual(steps, 25)  # 1 day + 1 hour in hours

    def test_map_time_to_steps_default_case(self):
        """Test the map_time_to_steps method for the default case where simpy_time_mapped_to is unsupported."""
        # Set simpy_time_mapped_to to None (unsupported mapping)
        DateTime.simpy_time_mapped_to = None

        # When simpy_time_mapped_to is None, steps_per_day should be None, leading to a logical failure
        # The method should return None or handle the case accordingly
        with self.assertRaises(TypeError):
            DateTime.map_time_to_steps(day=1, hour=1, minute=1, second=1)

    def test_map_time_to_steps_with_invalid_mapping(self):
        """Test map_time_to_steps with an invalid TimeComponent that should trigger the default case."""
        # Use an unsupported mapping (None or invalid enum value)
        DateTime.simpy_time_mapped_to = "unsupported"

        # Call the method and expect a TypeError or None due to the steps_per_day being None
        with self.assertRaises(TypeError):
            DateTime.map_time_to_steps(day=1, hour=1, minute=1, second=1)

    def test_edge_case_zero_time(self):
        """Test edge cases where the time passed is zero."""
        DateTime.map(TimeComponent.minute)
        result = DateTime.get(0)
        self.assertIn("0", result)  # Ensure delta is 0 minutes

        steps = DateTime.map_time_to_steps()
        self.assertEqual(steps, 0)  # Ensure steps calculation is 0 for zero time

    def test_get_method_with_unsupported_mapping(self):
        """Test the get method when simpy_time_mapped_to is not second, minute, or hour (default case)."""
        # Simulate an unsupported mapping by assigning None or an invalid enum value
        DateTime.simpy_time_mapped_to = None
        result = DateTime.get(10, time_string_from_initial_date=False)  # 10 should return a timedelta(0)
        self.assertEqual(result, "0:00:00")  # Unsupported case returns timedelta(0)


if __name__ == '__main__':
    unittest.main()
