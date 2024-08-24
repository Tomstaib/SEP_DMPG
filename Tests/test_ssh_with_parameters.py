import stat  # Built-in imports
import unittest
from unittest.mock import MagicMock, patch  # Standard library imports

from paramiko import SFTPClient  # Third-party imports
from paramiko.ssh_exception import SSHException

from ssh_with_parameters import (  # Local imports
    create_ssh_client,
    ensure_remote_directory,
    is_valid,
    transfer_file,
    transfer_folder
)


class TestCreateSSHClient(unittest.TestCase):
    @patch('paramiko.SSHClient')
    def test_create_ssh_client(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value

        server = MagicMock()
        port = 22
        user = MagicMock()
        password = MagicMock()
        client = create_ssh_client(server, port, user, password)

        mock_ssh_client.assert_called_once()
        mock_client.connect.assert_called_once_with(server, port, user, password)
        mock_client.load_system_host_keys.assert_called_once()
        mock_client.set_missing_host_key_policy.assert_called_once()

        self.assertEqual(client, mock_client)

    # Invalid Server Test
    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_server(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value
        mock_client.connect.side_effect = SSHException("Invalid Server")

        server = "invalid_server"
        port = 22
        user = MagicMock()
        password = MagicMock()
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)

    # Invalid User Test
    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_user(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value
        mock_client.connect.side_effect = SSHException("Invalid User")

        server = MagicMock()
        port = 22
        user = "invalid_user"
        password = MagicMock()
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)

    # Invalid Port Test
    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_port(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value
        mock_client.connect.side_effect = SSHException("Invalid Port")

        server = MagicMock()
        port = "Invalid Port"
        user = MagicMock()
        password = MagicMock()
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)

    # Invalid Password Test
    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_password(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value
        mock_client.connect.side_effect = SSHException("Invalid Password")

        server = MagicMock()
        port = 22
        user = MagicMock()
        password = "Invalid Password"
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)


class TestTransferFolder(unittest.TestCase):
    def test_is_valid(self):
        self.assertTrue(is_valid('valid_file.txt'))
        self.assertFalse(is_valid('.hidden_file'))
        self.assertFalse(is_valid('__pycache__/file.py'))

    @patch('paramiko.SFTPClient')  # Mock für den SFTPClient
    def test_ensure_remote_directory(self, mock_sftp_client):
        mock_sftp = mock_sftp_client.return_value
        # Simuliere, dass das Verzeichnis nicht existiert, indem wir stat einen IOError auslösen lassen
        mock_sftp.stat.side_effect = IOError

        # Aufruf der Funktion zur Absicherung des remote directories
        ensure_remote_directory(mock_sftp, 'remote_path')

        # Sicherstellung, dass mkdir richtig aufgerufen wird
        mock_sftp.mkdir.assert_called_once_with('remote_path')
        mock_sftp.chmod.assert_called_once_with('remote_path', stat.S_IRWXU)

    @patch('paramiko.SFTPClient')  # Mock für den SFTPClient
    def test_transfer_file(self, mock_sftp_client):
        mock_sftp = mock_sftp_client.return_value
        transfer_file(mock_sftp, 'local_path/file.txt', 'remote_path/file.txt')
        mock_sftp.put.assert_called_once_with('local_path/file.txt', 'remote_path/file.txt')

    @patch('paramiko.SSHClient')
    def test_transfer_folder(self, mock_ssh_client):
        # SFTP Mocken
        mock_sftp = MagicMock()
        mock_sftp_client = mock_ssh_client.return_value
        mock_sftp_client.open_sftp.return_value = mock_sftp

        # Mocken der Methoden von SFTP
        mock_sftp.stat.side_effect = IOError
        mock_sftp.mkdir = MagicMock()
        mock_sftp.chmod = MagicMock()
        mock_sftp.put = MagicMock()

        with patch('os.walk') as mock_os_walk:
            mock_os_walk.return_value = [
                ('/local/folder', ['src', 'other'], ['file1.txt']),
                ('/local/folder/src', [], ['file2.txt']),
            ]

        # Testen der Transferfolder Funktion
        transfer_folder(mock_ssh_client(), '/local/folder', '/remote/folder')

        mock_sftp.stat.assert_called_once_with('/remote/folder')
        mock_sftp.mkdir.assert_called_once_with('/remote/folder')
        mock_sftp.chmod.assert_called_once_with('/remote/folder', stat.S_IRWXU)
        mock_sftp.close.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
