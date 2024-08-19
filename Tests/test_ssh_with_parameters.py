import os.path
import unittest
import stat
from unittest.mock import patch, MagicMock
from paramiko.ssh_exception import SSHException
from ssh_with_parameters import create_ssh_client, transfer_folder, is_valid, ensure_remote_directory, transfer_file


#Testing if every method is called and equals the mock client
#Also testing what happens when a invalid user, server, port or password is given
class TestCreateSShClient(unittest.TestCase):
    @patch('paramiko.SSHClient')
    def test_create_ssh_client(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value

        server = 'valid Server'
        port = 22
        user = 'valid user'
        password = 'valid password'
        create_ssh_client(server, port, user, password)

        mock_ssh_client.assert_called_once()
        mock_client.connect.assert_called_once_with(server, port, user, password)
        mock_client.load_system_host_keys.assert_called_once()
        mock_client.set_missing_host_key_policy.assert_called_once()

    # Invalid Server Test
    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_server(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value
        mock_client.connect.side_effect = SSHException("Invalid Server")

        server = 'valid Server'
        port = 22
        user = 'valid user'
        password = 'valid password'
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)

    # Invalid User Test
    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_user(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value
        mock_client.connect.side_effect = SSHException("Invalid User")

        server = 'valid Server'
        port = 22
        user = "invalid_user"
        password = 'valid password'
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)

    # Invalid Port Test
    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_port(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value
        mock_client.connect.side_effect = SSHException("Invalid Port")

        server = 'valid Server'
        port = "Invalid Port"
        user = 'valid user'
        password = 'valid password'
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)

    # Invalid Password Test
    @patch('paramiko.SSHClient')
    def test_create_ssh_client_invalid_password(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value
        mock_client.connect.side_effect = SSHException("Invalid Password")

        server = 'valid Server'
        port = 22
        user = 'valid user'
        password = "Invalid Password"
        with self.assertRaises(SSHException):
            create_ssh_client(server, port, user, password)


class TestIsValid(unittest.TestCase):

    def test_is_valid(self):
        test_path = MagicMock()

        self.assertTrue(is_valid(test_path))
        self.assertFalse(is_valid('.test_datei'))
        self.assertFalse(is_valid('__pycache__'))
        self.assertTrue(is_valid('src'))
        self.assertTrue(is_valid('test_order'))


class TestEnsureRemoteDirectory(unittest.TestCase):
    @patch('paramiko.SFTPClient')
    def test_ensure_remote_directory_available(self, mock_sftp_client):
        mock_sftp_client = mock_sftp_client.return_value
        mock_sftp_client.connect.side_effect = None

        mock_sftp_client.stat.return_value = MagicMock()

        test_remote_path = 'remote_path'
        ensure_remote_directory(mock_sftp_client, test_remote_path)

        mock_sftp_client.stat.assert_called_once_with(test_remote_path)
        mock_sftp_client.mkdir.assert_not_called()
        mock_sftp_client.chmod.assert_not_called()

    @patch('paramiko.SSHClient')
    def test_ensure_remote_directory_missing(self, mock_ssh_client):
        mock_sftp_client = mock_ssh_client.return_value

        mock_sftp_client.stat.side_effect = IOError

        test_remote_path = 'remote_path'

        ensure_remote_directory(mock_sftp_client, test_remote_path)

        mock_sftp_client.stat.assert_called_once_with(test_remote_path)
        mock_sftp_client.mkdir.assert_called_once_with(test_remote_path)
        mock_sftp_client.chmod.assert_called_once_with(test_remote_path, stat.S_IRWXU)


class TestTransfer(unittest.TestCase):

    @patch('paramiko.SSHClient')
    @patch('os.walk')
    def test_transfer_folder(self, mock_sftp_client, mock_os_walk):
        mock_ssh_client = mock_sftp_client.return_value
        # SFTP Mocken
        mock_sftp_client = mock_ssh_client.return_value.open_sftp.return_value

        # Mocken der Methoden von sftp
        mock_sftp_client.stat.side_effect = None
        mock_sftp_client.mkdir = MagicMock()
        mock_sftp_client.chmod = MagicMock()
        mock_sftp_client.put = MagicMock()

        mock_os_walk.return_value = [
            ('/local/folder', ['src', 'other', 'local'], ['file1.txt', 'text1.docx', 'test4.html']),
            ('/local/folder/src', [], ['file2.txt']),
        ]
        # Testen der Transferfolder Funktion
        transfer_folder(mock_ssh_client(), '/local/folder', '/remote/folder')


        mock_sftp_client.close.assert_called_once_with()




if __name__ == '__main__':
    unittest.main()
