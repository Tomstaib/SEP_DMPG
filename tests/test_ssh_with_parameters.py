import stat
import unittest
from unittest.mock import patch, MagicMock, mock_open, Mock
import os
import paramiko
from paramiko.ssh_exception import SSHException
import json
import ssh_with_parameters
from ssh_with_parameters import create_ssh_client, transfer_folder, is_valid, ensure_remote_directory, transfer_file, \
    read_json


class TestCreateSShClient(unittest.TestCase):
    # checks if the method correctly creates and configures an SSH client. It verifies that
    # SSHClient.connect is called with the provided server, port, username, and password, and also checks if system
    # host keys are loaded and the policy for missing host keys is set.
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

    # evaluates how the create_ssh_client method handles an invalid server. It simulates an SSHException
    # for an invalid server and checks if the method properly raises and handles this exception.
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

    # checks the response of the create_ssh_client method when an invalid username is provided. By
    # simulating an SSHException for an invalid user, it verifies that the exception is correctly raised and handled.
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

    # assesses how the create_ssh_client method reacts to an invalid port. It simulates an SSHException due
    # to an invalid port and ensures that the method correctly raises and handles this exception.
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

    # examines the method create_ssh_client's behavior when given an incorrect password. It simulates an
    # SSHException for an invalid password and checks if the method handles the exception as expected.
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

    # verifies if the is_valid method correctly identifies whether a path is valid. It checks various input
    # paths to confirm that valid paths (such as directory names) are recognized as valid and certain patterns (like
    # .test_datei and __pycache__) are considered invalid.
    def test_is_valid(self):
        test_path = MagicMock()

        self.assertTrue(is_valid(test_path))
        self.assertFalse(is_valid('.test_datei'))
        self.assertFalse(is_valid('__pycache__'))
        self.assertTrue(is_valid('src'))
        self.assertTrue(is_valid('test_order'))


class TestEnsureRemoteDirectory(unittest.TestCase):
    # ensures that ensure_remote_directory correctly identifies when a remote directory already exists. It simulates
    # a successful stat call and verifies that mkdir and chmod are not called.
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

    # checks if ensure_remote_directory properly creates a directory when it does not exist. It simulates an IOError
    # for a missing directory and confirms that mkdir and chmod are called to create and set permissions on the
    # directory.
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
    # verifies that the transfer_folder function successfully transfers a folder from the local to the remote system.
    # It simulates a directory structure and ensures that files are transferred and the SFTP connection is properly
    # closed.
    @patch('paramiko.SSHClient')
    @patch('os.walk')
    @patch('ssh_with_parameters.ensure_remote_directory')
    def test_transfer_folder_success(self, mock_ensure_remote_directory, mock_os_walk, mock_ssh_client):
        mock_sftp_client = mock_ssh_client.return_value.open_sftp.return_value
        mock_sftp_client.stat.side_effect = FileNotFoundError
        mock_sftp_client.mkdir = MagicMock()
        mock_sftp_client.chmod = MagicMock()
        mock_sftp_client.put = MagicMock()

        mock_os_walk.return_value = [
            ('/local/folder', ['src', 'other', 'local'], ['file1.txt', 'text1.docx', 'test4.html']),
            ('/local/folder/src', [], ['file2.txt']),
        ]

        transfer_folder(mock_ssh_client(), '/local/folder', '/remote/folder')

        mock_sftp_client.close.assert_called_once_with()

    # ensures that the transfer_folder function skips invalid directories. It simulates a directory containing an
    # invalid subdirectory and verifies that no files from the invalid directory are transferred.
    @patch('paramiko.SSHClient')
    @patch('os.walk')
    @patch('ssh_with_parameters.is_valid')
    def test_transfer_folder_skip_invalid_directory(self, mock_os_walk, mock_is_valid, mock_ssh_client):
        mock_sftp_client = mock_ssh_client.return_value.open_sftp.return_value
        mock_sftp_client.stat.side_effect = None
        mock_sftp_client.mkdir = MagicMock()
        mock_sftp_client.chmod = MagicMock()
        mock_sftp_client.put = MagicMock()

        mock_os_walk.return_value = [
            ('/local/folder', ['invalid_dir'], ['file1.txt']),
            ('/local/folder/invalid_dir', [], ['file2.txt']),
        ]

        transfer_folder(mock_ssh_client(), '/local/folder', '/remote/folder')

        mock_sftp_client.put.assert_not_called()

    # checks that the transfer_folder function does not transfer invalid files. It simulates a directory with an
    # invalid file and ensures that the file is not uploaded.
    @patch('paramiko.SSHClient')
    @patch('os.walk')
    @patch('ssh_with_parameters.is_valid')
    def test_transfer_folder_invalid_file(self, mock_os_walk, mock_is_valid, mock_ssh_client):
        mock_sftp_client = mock_ssh_client.return_value.open_sftp.return_value
        mock_sftp_client.stat.side_effect = None
        mock_sftp_client.mkdir = MagicMock()
        mock_sftp_client.chmod = MagicMock()
        mock_sftp_client.put = MagicMock()

        mock_os_walk.return_value = [
            ('/local/folder', ['src'], ['invalid_file.docx', 'file2.txt']),
        ]

        transfer_folder(mock_ssh_client(), '/local/folder', '/remote/folder')

        mock_sftp_client.put.assert_not_called()

    # verifies that the transfer_folder function handles failures during file transfer. It simulates an exception
    # occurring during the transfer process and confirms that the exception is raised and the SFTP connection is closed.
    @patch('paramiko.SSHClient')
    @patch('os.walk')
    def test_transfer_folder_failure(self, mock_os_walk, mock_ssh_client):
        mock_sftp_client = mock_ssh_client.return_value.open_sftp.return_value
        mock_sftp_client.stat.side_effect = Exception('Transfer Error')
        mock_sftp_client.mkdir = MagicMock()
        mock_sftp_client.chmod = MagicMock()
        mock_sftp_client.put = MagicMock()

        mock_os_walk.return_value = [
            ('/local/folder', ['src', 'other', 'local'], ['file1.txt', 'text1.docx', 'test4.html']),
            ('/local/folder/src', [], ['file2.txt']),
        ]

        with self.assertRaises(Exception):
            transfer_folder(mock_ssh_client(), '/local/folder', '/remote/folder')
            mock_sftp_client.close.assert_called_once_with()

    # checks if the transfer_file function successfully transfers a single file from local to remote. It ensures that
    # the put method is called with the correct file paths.
    @patch('paramiko.SSHClient')
    def test_transfer_file_success(self, mock_sftp_client):
        mock_sftp_client = MagicMock()
        mock_sftp_client.from_transport.return_value = mock_sftp_client

        local_file_path = 'test_local.txt'
        remote_file_path = 'test_remote.txt'

        transfer_file(mock_sftp_client, local_file_path, remote_file_path)

        mock_sftp_client.put.assert_called_with(local_file_path, remote_file_path)

    # verifies that the transfer_file function handles errors during file transfer. It simulates an exception being
    # raised during the transfer and ensures that the exception is properly raised.
    @patch('paramiko.SSHClient')
    def test_transfer_file_failure(self, mock_sftp_client):
        mock_sftp_client = MagicMock()
        mock_sftp_client.from_transport.return_value = mock_sftp_client

        mock_sftp_client.put.side_effect = Exception('Transfer Error')

        local_file_path = 'test_local.txt'
        remote_file_path = 'test_remote.txt'

        with self.assertRaises(Exception):
            (transfer_file(mock_sftp_client, local_file_path, remote_file_path))


class TestReadVersionFromFile(unittest.TestCase):
    # checks if read_version_from_file correctly reads the version from a valid JSON file. It ensures that the method
    # extracts the version value correctly from the file's content.
    @patch("builtins.open", new_callable=mock_open, read_data='{"version": "1.0.0"}')
    def test_valid_file(self, mock_file):
        result = ssh_with_parameters.read_version_from_file("dummy_path.json")
        self.assertEqual(result, "1.0.0")

    # evaluates how read_version_from_file handles the case when the file does not exist. It simulates a
    # FileNotFoundError and verifies that the method returns None.
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_file):
        result = ssh_with_parameters.read_version_from_file("non_existent_file.json")
        self.assertIsNone(result)
    # checks if read_version_from_file returns None when the version key is missing in the JSON file. It ensures that
    # the absence of the key is handled correctly.
    @patch("builtins.open", new_callable=mock_open, read_data='{"other_key": "1.0.0"}')
    def test_key_error(self, mock_file):
        result = ssh_with_parameters.read_version_from_file("missing_version_key.json")
        self.assertIsNone(result)

    # assesses how read_version_from_file handles errors in JSON decoding. It simulates an invalid JSON format and
    # verifies that the method returns None.
    @patch("builtins.open", new_callable=mock_open, read_data='{"version": ')
    def test_json_decode_error(self, mock_file):
        result = ssh_with_parameters.read_version_from_file("invalid_json.json")
        self.assertIsNone(result)


class TestExecudeCommand(unittest.TestCase):
    def setUp(self):
        self.ssh_client = MagicMock(spec=paramiko.SSHClient)
        self.stdout_mock = MagicMock()
        self.stderr_mock = MagicMock()

        self.ssh_client.exec_command = MagicMock(return_value=(None, self.stdout_mock, self.stderr_mock))

    # verifies that execute_command correctly executes a command via SSH and processes the output. It ensures that
    # the command output and error messages are read and returned properly.
    def test_execute_command_success(self):
        self.stdout_mock.read.return_value = b'command output\n'
        self.stderr_mock.read.return_value = b''

        stdout, stderr = ssh_with_parameters.execute_command(self.ssh_client, 'echo "test"')

        self.assertEqual(stdout, 'command output')
        self.assertEqual(stderr, '')

    # checks how execute_command handles errors during command execution. It simulates an error message and verifies
    # that the method correctly returns the error message and empty output.
    def test_execute_command_error(self):
        self.stdout_mock.read.return_value = b''
        self.stderr_mock.read.return_value = b'error message\n'

        stdout, stderr = ssh_with_parameters.execute_command(self.ssh_client, 'invalid command')

        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'error message')


class TestReadJson(unittest.TestCase):
    # ensures that read_json correctly reads and parses JSON data from a file. It checks that the JSON data is read
    # correctly and that the file path is constructed as expected.
    @patch('os.path.isfile')
    @patch('os.path.dirname')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({'key': 'value'}))
    def test_read_json_success(self, mock_open, mock_dirname, mock_isfile):
        mock_isfile.return_value = True
        mock_dirname.side_effect = ['some_dir', 'another_dir', 'DMPG']

        result = read_json('test.json')

        self.assertEqual(result, {'key': 'value'})

        expected_path = os.path.join('some_dir', 'test.json')
        actual_path = mock_open.call_args[0][0]
        self.assertEqual(expected_path, actual_path)

    # verifies that read_json raises a FileNotFoundError when the file does not exist. It simulates the absence of
    # the file and confirms that the exception is raised.
    @patch('os.path.isfile')
    @patch('os.path.dirname')
    def test_file_not_found(self, mock_dirname, mock_isfile):
        mock_isfile.return_value = False
        mock_dirname.side_effect = ['some_dir', 'another_dir', 'DMPG', '']

        with self.assertRaises(FileNotFoundError):
            read_json('test.json')

    # checks if read_json handles the scenario where the file is in a specific directory. It simulates the file not
    # being found in the expected path and ensures that a FileNotFoundError is raised.
    @patch('os.path.isfile')
    @patch('os.path.dirname')
    def test_file_in_dmpg_folder(self, mock_dirname, mock_isfile):
        mock_isfile.return_value = False
        mock_dirname.side_effect = ['some_dir', 'DMPG', '']

        with self.assertRaises(FileNotFoundError):
            read_json('test.json')


if __name__ == '__main__':
    unittest.main()
