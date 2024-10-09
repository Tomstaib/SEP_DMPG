import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import logging
import requests

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Laufzeitprognose/src')
))

from util.runtime_prediction import send_progress_to_server, save_progress

class TestRuntimePrediction(unittest.TestCase):

    @patch('util.runtime_prediction.requests.post')  # Adjusted patch target
    def test_send_progress_to_server_success(self, mock_post):
        """Test successful progress send to server."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        ct = ['50%', '[time computed] 0:00:05', '[time to complete] 0:00:10',
              '[time prediction] 0:00:15', '[time per iteration] 0:00:02']
        send_progress_to_server(ct, i=4, step=1, num_replications=10)

        mock_post.assert_called_once()

    @patch('util.runtime_prediction.requests.post')  # Adjusted patch target
    def test_send_progress_to_server_http_error(self, mock_post):
        """Test HTTP error handling during progress send to the server."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Mock HTTP error with status code 500"
        )
        mock_post.return_value = mock_response

        ct = ['50%', '[time computed] 0:00:05', '[time to complete] 0:00:10',
              '[time prediction] 0:00:15', '[time per iteration] 0:00:02']
        with self.assertLogs(level='ERROR') as log:
            send_progress_to_server(ct, i=4, step=1, num_replications=10)
            self.assertGreater(len(log.output), 0)
            self.assertIn(
                "HTTP error occurred while sending Runtime-Prediction: Mock HTTP error with status code 500",
                log.output[0]
            )

    @patch('util.runtime_prediction.requests.post')  # Adjusted patch target
    def test_send_progress_to_server_request_exception(self, mock_post):
        """Test general request exception handling."""
        mock_post.side_effect = requests.exceptions.RequestException("Mock request exception")

        ct = ['50%', '[time computed] 0:00:05', '[time to complete] 0:00:10',
              '[time prediction] 0:00:15', '[time per iteration] 0:00:02']
        with self.assertLogs(level='ERROR') as log:
            send_progress_to_server(ct, i=4, step=1, num_replications=10)
            self.assertGreater(len(log.output), 0)
            self.assertIn(
                "Request error occurred while sending Runtime-Prediction: Mock request exception",
                log.output[0]
            )

    @patch('util.runtime_prediction.requests.post')  # Adjusted patch target
    def test_send_progress_to_server_unexpected_error(self, mock_post):
        """Test unexpected error handling during progress send to the server."""
        mock_post.side_effect = Exception("Mock unexpected exception")

        ct = ['50%', '[time computed] 0:00:05', '[time to complete] 0:00:10',
              '[time prediction] 0:00:15', '[time per iteration] 0:00:02']
        with self.assertLogs(level='ERROR') as log:
            send_progress_to_server(ct, i=4, step=1, num_replications=10)
            self.assertGreater(len(log.output), 0)
            self.assertIn(
                "An unexpected error occurred: Mock unexpected exception",
                log.output[0]
            )

if __name__ == '__main__':
    unittest.main()
