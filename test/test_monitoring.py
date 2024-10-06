import pytest
from unittest.mock import patch, MagicMock
import psutil
from Laufzeitprognose.monitoring import monitor_resources


class TestMonitorResources:
    """
    Test class to validate the functionality of the 'monitor_resources' function.
    As a Wirtschaftsinformatik student, the goal is to ensure the system monitoring
    tool behaves as expected under various conditions such as normal operations,
    edge cases, and interruptions.
    """

    @patch("Laufzeitprognose.monitoring.psutil.cpu_percent")
    @patch("Laufzeitprognose.monitoring.psutil.virtual_memory")
    @patch("builtins.print")
    @patch("time.sleep", return_value=None)  # Prevent actual sleeping during the test
    def test_monitor_resources(self, mock_sleep, mock_print, mock_virtual_memory, mock_cpu_percent):
        """
        Tests the basic functionality of the 'monitor_resources' function by simulating
        CPU and RAM usage, ensuring correct output, and verifying that no unwanted
        messages are printed.
        """
        mock_cpu_percent.return_value = [50.0] * psutil.cpu_count()
        mock_virtual_memory.return_value = MagicMock(percent=70, used=8 * (1024 ** 3), total=16 * (1024 ** 3))

        monitor_resources(interval=1, max_iterations=1)

        mock_print.assert_any_call(
            f"CPU Usage: {[50.0] * psutil.cpu_count()}%, RAM Usage: 70% (Used: 8.00 GB, Total: 16.00 GB)"
        )

        calls = [call.args[0] for call in mock_print.call_args_list]
        assert "Monitoring stopped." not in calls

    @patch("Laufzeitprognose.monitoring.psutil.cpu_percent")
    @patch("Laufzeitprognose.monitoring.psutil.virtual_memory")
    @patch("time.sleep", return_value=None)  # Mock time.sleep to avoid delays
    @patch("builtins.print")
    def test_monitor_resources_sleep(self, mock_print, mock_sleep, mock_virtual_memory, mock_cpu_percent):
        """
        Validates that 'time.sleep' is called correctly during monitoring. This is
        important to ensure the system waits for the given interval between monitoring checks.
        """
        mock_cpu_percent.return_value = [50.0] * psutil.cpu_count()
        mock_virtual_memory.return_value = MagicMock(percent=70, used=8 * (1024 ** 3), total=16 * (1024 ** 3))

        monitor_resources(interval=5, max_iterations=2)

        mock_sleep.assert_called_with(5)

        assert mock_sleep.call_count >= 1

    @patch("Laufzeitprognose.monitoring.psutil.cpu_percent")
    @patch("Laufzeitprognose.monitoring.psutil.virtual_memory")
    @patch("builtins.print")
    @patch("time.sleep", return_value=None)  # Mock time.sleep to avoid delays
    def test_monitor_resources_edge_case(self, mock_sleep, mock_print, mock_virtual_memory, mock_cpu_percent):
        """
        Tests an edge case where the system has 0% CPU usage and minimal RAM usage.
        This ensures the monitoring tool handles extreme conditions gracefully.
        """
        mock_cpu_percent.return_value = [0.0] * psutil.cpu_count()
        mock_virtual_memory.return_value = MagicMock(percent=1, used=0.1 * (1024 ** 3), total=16 * (1024 ** 3))

        monitor_resources(interval=1, max_iterations=1)

        mock_print.assert_any_call(
            f"CPU Usage: {[0.0] * psutil.cpu_count()}%, RAM Usage: 1% (Used: 0.10 GB, Total: 16.00 GB)"
        )

        calls = [call.args[0] for call in mock_print.call_args_list]
        assert "Monitoring stopped." not in calls

    @patch("Laufzeitprognose.monitoring.psutil.cpu_percent")
    @patch("Laufzeitprognose.monitoring.psutil.virtual_memory")
    @patch("builtins.print")
    @patch("time.sleep", return_value=None)  # Prevent delays during the test
    def test_monitor_resources_keyboard_interrupt(self, mock_sleep, mock_print, mock_virtual_memory, mock_cpu_percent):
        """
        Tests the handling of a KeyboardInterrupt to ensure that the function gracefully
        stops monitoring when interrupted.
        """
        mock_cpu_percent.return_value = [50.0] * psutil.cpu_count()
        mock_virtual_memory.return_value = MagicMock(percent=70, used=8 * (1024 ** 3), total=16 * (1024 ** 3))

        with patch("Laufzeitprognose.monitoring.psutil.cpu_percent", side_effect=KeyboardInterrupt):
            monitor_resources(interval=1)

        mock_print.assert_any_call("Monitoring stopped.")

    def test_monitor_resources_negative_interval(self):
        """
        Ensures that a ValueError is raised if the interval for monitoring is set
        to a negative value. This validates proper input validation in the function.
        """
        with pytest.raises(ValueError):
            monitor_resources(interval=-1, max_iterations=1)
