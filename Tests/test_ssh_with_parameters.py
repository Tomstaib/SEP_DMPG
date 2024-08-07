import unittest
from unittest.mock import patch, MagicMock
from ssh_with_parameters import create_ssh_client


class TestCreateSShClient(unittest.TestCase):
    @patch('paramiko.SSHClient')
    def test_create_ssh_client(self, MockSSHClient):
        #Create instance of Mock-SSH-Clients
        mock_client = MockSSHClient.return_value

        #Call the function
        server = MagicMock()
        port = 22
        user = MagicMock()
        password = MagicMock()
        client = create_ssh_client(server, port, user, password)

        #Testin if paramiko.SSHClient() is called
        MockSSHClient.assert_called_once()

        #Testing if the connect method is called with correct parameters
        mock_client.connect.assert_called_once_with(server, port, user, password)

        mock_client.load_system_host_keys.assert_called_once()
        mock_client.set_missing_host_key.assert_called_once()

        self.assertEqual(client, mock_client)


