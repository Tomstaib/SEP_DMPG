import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import requests
import logging

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Laufzeitprognose/src')
))

from util.runtime_prediction import send_progress_to_server, save_progress, MockResponse


class TestRuntimePrediction(unittest.TestCase):

    @patch('Laufzeitprognose.src.util.runtime_prediction.requests.post')
    def test_send_progress_to_server_success(self, mock_post):
        """Test successful progress send to server."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None  
        mock_post.return_value = mock_response

        ct = ['50%', '[time computed] 0:00:05', '[time to complete] 0:00:10',
              '[time prediction] 0:00:15', '[time per iteration] 0:00:02']
        send_progress_to_server(ct, i=4, step=1, num_replications=10)

        mock_post.assert_called_once()

    @patch('Laufzeitprognose.src.util.runtime_prediction.requests.post')
    def test_send_progress_to_server_http_error(self, mock_post):
        """Test HTTP error handling during progress send to the server."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Mock HTTP error with status code 500")
        mock_post.return_value = mock_response

        ct = ['50%', '[time computed] 0:00:05', '[time to complete] 0:00:10',
              '[time prediction] 0:00:15', '[time per iteration] 0:00:02']
        with self.assertLogs(level='ERROR') as log:
            send_progress_to_server(ct, i=4, step=1, num_replications=10)
            self.assertIn("HTTP error occurred while sending Runtime-Prediction: Mock HTTP error with status code 500", log.output[0])

    @patch('Laufzeitprognose.src.util.runtime_prediction.requests.post')
    def test_send_progress_to_server_request_exception(self, mock_post):
        """Test general request exception handling."""
        mock_post.side_effect = requests.exceptions.RequestException("Mock request exception")

        ct = ['50%', '[time computed] 0:00:05', '[time to complete] 0:00:10',
              '[time prediction] 0:00:15', '[time per iteration] 0:00:02']
        with self.assertLogs(level='ERROR') as log:
            send_progress_to_server(ct, i=4, step=1, num_replications=10)
            self.assertIn("Request error occurred while sending Runtime-Prediction: Mock request exception", log.output[0])

    @patch('Laufzeitprognose.src.util.runtime_prediction.requests.post')
    def test_send_progress_to_server_unexpected_error(self, mock_post):
        """Test unexpected error handling during progress send to the server."""
        mock_post.side_effect = Exception("Mock unexpected exception")

        ct = ['50%', '[time computed] 0:00:05', '[time to complete] 0:00:10',
              '[time prediction] 0:00:15', '[time per iteration] 0:00:02']
        with self.assertLogs(level='ERROR') as log:
            send_progress_to_server(ct, i=4, step=1, num_replications=10)
            self.assertIn("An unexpected error occurred: Mock unexpected exception", log.output[0])

    def test_save_progress_success(self):
        """Test successful execution of save_progress."""
        ct = ['50%', '[time computed] 0:00:05', '[time to complete] 0:00:10',
              '[time prediction] 0:00:15', '[time per iteration] 0:00:02']
        data = save_progress(ct, i=4, step=1, num_replications=10)

        expected_data = {
            "percentage": '50%',
            "time_computed": '0:00:05',
            "time_to_complete": '0:00:10',
            "time_prediction": '0:00:15',
            "time_per_iteration": '0:00:02',
            "current_iteration": 5,
            "total_iterations": 10
        }

        self.assertEqual(data, expected_data)

    def test_save_progress_index_error(self):
        """Test save_progress handling of IndexError."""
        ct = ['50%', '[time computed] 0:00:05']
        with self.assertLogs(level='ERROR') as log:
            data = save_progress(ct, i=4, step=1, num_replications=10)
            self.assertIn("Error accessing ct elements", log.output[0])
            self.assertIsNone(data)

    def test_save_progress_attribute_error(self):
        """Test save_progress handling of AttributeError."""
        ct = [None, None, None, None, None]
        with self.assertLogs(level='ERROR') as log:
            data = save_progress(ct, i=4, step=1, num_replications=10)
            self.assertIn("Error processing string attributes", log.output[0])
            self.assertIsNone(data)

    def test_save_progress_unexpected_error(self):
        """Test save_progress handling of unexpected error."""
        mock_ct = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_ct[0].replace.side_effect = Exception("Mock unexpected exception")

        with self.assertLogs(level='ERROR') as log:
            data = save_progress(mock_ct, i=4, step=1, num_replications=10)
            self.assertIn("ERROR:root:Unknown error: Mock unexpected exception", log.output[0])
            self.assertIsNone(data)


class TestMockResponse(unittest.TestCase):

    def test_raise_for_status_success(self):
        """Test that raise_for_status does not raise an error when status code is 200."""
        response = MockResponse(200) 
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            self.fail("HTTPError was unexpectedly raised for status code 200")

    def test_raise_for_status_http_error(self):
        """Test that raise_for_status raises an HTTPError when status code is not 200."""
        response = MockResponse(404)
        with self.assertRaises(requests.exceptions.HTTPError):
            response.raise_for_status()


class TestSendProgressToServer(unittest.TestCase):

    @patch('Laufzeitprognose.src.util.runtime_prediction.save_progress', return_value=None)  # Mocking save_progress to return None
    def test_send_progress_to_server_data_is_none(self, mock_save_progress):
        """Test send_progress_to_server when save_progress returns None."""
        with self.assertLogs(level='ERROR') as log:
            send_progress_to_server(ct=[], i=0, step=1, num_replications=10)
            self.assertIn("ERROR:root:Failed to save progress data. Data is None.", log.output)

        mock_save_progress.assert_called_once()


if __name__ == '__main__':
    unittest.main()
