import unittest
from unittest.mock import patch, MagicMock
import json
import os
import shutil
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from util.agent_server import app, AGENTS_DIR, BASE_DIR


class TestAgentServer(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

        # Create a temporary directory for agents within the project directory
        self.temp_agents_dir = os.path.join(BASE_DIR, "temp_agents")
        if not os.path.exists(self.temp_agents_dir):
            os.makedirs(self.temp_agents_dir)

        # Patch the AGENTS_DIR
        self.agents_dir_patcher = patch('util.agent_server.AGENTS_DIR', self.temp_agents_dir)
        self.agents_dir_patcher.start()

    def tearDown(self):
        # Remove the temporary directory and its contents
        if os.path.exists(self.temp_agents_dir):
            shutil.rmtree(self.temp_agents_dir)
        self.agents_dir_patcher.stop()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Generate Agent', response.data)

    @patch('util.agent_server.shutil.rmtree')
    @patch('util.agent_server.os.path.exists')
    @patch('util.agent_server.os.remove')
    @patch('util.agent_server.uuid.uuid4')
    @patch('util.agent_server.subprocess.run')
    @patch('util.agent_server.os.makedirs')
    def test_generate_agent(self, mock_makedirs, mock_subprocess, mock_uuid, mock_remove, mock_exists, mock_rmtree):
        mock_uuid.return_value = 'test-uuid'
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_remove.side_effect = None  # Don't actually remove anything
        mock_exists.return_value = False  # Simulate that directories don't exist
        mock_rmtree.side_effect = None  # Don't actually remove directories

        # Simulate an exception being raised when os.makedirs is called
        mock_makedirs.side_effect = PermissionError("Access is denied")

        response = self.client.post('/generate_agent')
        self.assertEqual(response.status_code, 500)

    @patch('util.agent_server.os.path.exists')
    @patch('util.agent_server.send_file')
    def test_download_agent(self, mock_send_file, mock_exists):
        mock_exists.return_value = True
        mock_send_file.return_value = 'Mocked file'

        response = self.client.get('/download/test-uuid')
        self.assertEqual(response.status_code, 200)
        mock_send_file.assert_called_once()

    @patch('util.agent_server.valid_api_keys', {'test-api-key': True})
    def test_receive_data_valid_key(self):
        data = {
            'hostname': 'test-host',
            'ip_address': '127.0.0.1'
        }
        headers = {'Authorization': 'Bearer test-api-key'}
        response = self.client.post('/receive_data',
                                    data=json.dumps(data),
                                    content_type='application/json',
                                    headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Data received successfully', response.data)
        from util.agent_server import valid_api_keys
        self.assertNotIn('test-api-key', valid_api_keys)

    def test_receive_data_invalid_key(self):
        data = {
            'hostname': 'test-host',
            'ip_address': '127.0.0.1'
        }
        headers = {'Authorization': 'Bearer invalid-key'}
        response = self.client.post('/receive_data',
                                    data=json.dumps(data),
                                    content_type='application/json',
                                    headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Invalid API key', response.data)

    def test_receive_data_missing_data(self):
        data = {'hostname': 'test-host'}  # Missing ip_address
        headers = {'Authorization': 'Bearer test-api-key'}
        with patch('util.agent_server.valid_api_keys', {'test-api-key': True}):
            response = self.client.post('/receive_data',
                                        data=json.dumps(data),
                                        content_type='application/json',
                                        headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Hostname or IP address missing', response.data)


if __name__ == '__main__':
    unittest.main()
