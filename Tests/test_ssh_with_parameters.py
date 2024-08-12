import unittest
from unittest.mock import patch, MagicMock

from paramiko.ssh_exception import SSHException

from ssh_with_parameters import create_ssh_client

#Testing if every method is called and equals the mock client
#Also testing what happens when a invalid user, server, port or password is given
class TestCreateSShClient(unittest.TestCase):
    @patch('paramiko.SSHClient')
    def test_create_ssh_client(self, MockSSHClient):
        mock_client = MockSSHClient.return_value

        server = MagicMock()
        port = MagicMock()
        user = MagicMock()
        password = MagicMock()
        client = create_ssh_client(server, port, user, password)

        MockSSHClient.assert_called_once()
        mock_client.connect.assert_called_once_with(server, port, user, password)
        mock_client.load_system_host_keys.assert_called_once()
        mock_client.set_missing_host_key_policy.assert_called_once()

        self.assertEqual(client, mock_client)

    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_server(self, MockSSHClient):
        mock_client = MockSSHClient.return_value
        mock_client.connect.side_effect = SSHException("Invalid Server")

        server = "invalid_server"
        port = MagicMock()
        user = MagicMock()
        password = MagicMock()
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)

    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_user(self, MockSSHClient):
        mock_client = MockSSHClient.return_value
        mock_client.connect.side_effect = SSHException("Invalid User")

        server = MagicMock()
        port = MagicMock()
        user = "invalid_user"
        password = MagicMock()
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)

    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_port(self, MockSSHClient):
        mock_client = MockSSHClient.return_value
        mock_client.connect.side_effect = SSHException("Invalid Port")

        server = MagicMock()
        port = "Invalid Port"
        user = MagicMock()
        password = MagicMock()
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)

    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_password(self, MockSSHClient):
        mock_client = MockSSHClient.return_value
        mock_client.connect.side_effect = SSHException("Invalid Password")

        server = MagicMock()
        port = MagicMock()
        user = MagicMock()
        password = "Invalid Password"
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)


if __name__ == '__main__':
    unittest.main()
