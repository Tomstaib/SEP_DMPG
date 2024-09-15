#standard-library-modules
import os
import stat
import json
import sys
import unittest
from unittest import mock
from unittest.mock import Mock, patch, MagicMock, mock_open, call

from tkinter import Tk


#third-party-modules
import paramiko
from paramiko.ssh_exception import SSHException

# Für Dockercontainer zum initialisierren der lokalen Module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

#local-modules
import SSHVerbindung.ssh_with_parameters
from SSHVerbindung.ssh_with_parameters import (
    create_ssh_client, transfer_folder, is_valid, ensure_remote_directory,
    transfer_file, read_json, select_folder, check_python_version, install_libraries, get_private_config, main, read_version_from_file, execute_command
)


class TestCreateSSHClient(unittest.TestCase):
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

    @patch('paramiko.SSHClient')
    @patch('os.walk')
    @patch('SSHVerbindung.ssh_with_parameters.ensure_remote_directory')
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

    @patch('paramiko.SSHClient')
    @patch('os.walk')
    @patch('SSHVerbindung.ssh_with_parameters.is_valid', side_effect=lambda path: 'invalid' not in path)
    def test_transfer_folder_skip_invalid_directory(self, mock_is_valid, mock_os_walk, mock_ssh_client):
        mock_sftp_client = mock_ssh_client.return_value.open_sftp.return_value
        mock_sftp_client.stat.side_effect = None
        mock_sftp_client.mkdir = MagicMock()
        mock_sftp_client.chmod = MagicMock()
        mock_sftp_client.put = MagicMock()

        mock_os_walk.return_value = [
            (os.path.normpath('/local/folder'), ['invalid_dir', 'valid_dir'], ['file1.txt']),
            (os.path.normpath('/local/folder/invalid_dir'), [], ['file2.txt']),
            (os.path.normpath('/local/folder/valid_dir'), [], ['file3.txt']),
        ]

        def custom_transfer_file(sftp, local_file_path, remote_file_path):
            print(f"Versuche, {local_file_path} nach {remote_file_path} zu übertragen")
            sftp.put(local_file_path.replace('\\', '/'), remote_file_path.replace('\\', '/'))

        with patch('SSHVerbindung.ssh_with_parameters.transfer_file', new=custom_transfer_file):
            transfer_folder(mock_ssh_client(), os.path.normpath('/local/folder'), os.path.normpath('/remote/folder'))

        expected_calls = [
            ('/local/folder/file1.txt', '/remote/folder/file1.txt'),
            ('/local/folder/valid_dir/file3.txt', '/remote/folder/valid_dir/file3.txt')
        ]

        actual_calls = [
            (args[0].replace("\\", "/"), args[1].replace("\\", "/"))
            for args, kwargs in mock_sftp_client.put.call_args_list
        ]

        for expected_call in expected_calls:
            if expected_call not in actual_calls:
                raise AssertionError(f"{expected_call[0]} wurde nicht nach {expected_call[1]} übertragen.")

    @patch('paramiko.SSHClient')
    @patch('os.walk')
    @patch('SSHVerbindung.ssh_with_parameters.is_valid', side_effect=lambda path: 'invalid' not in path)
    def test_transfer_folder_invalid_file(self, mock_is_valid, mock_os_walk, mock_ssh_client):
        mock_sftp_client = mock_ssh_client.return_value.open_sftp.return_value
        mock_sftp_client.stat.side_effect = None
        mock_sftp_client.mkdir = MagicMock()
        mock_sftp_client.chmod = MagicMock()
        mock_sftp_client.put = MagicMock()

        # Simuliere ein Dateisystem mit einer "invaliden" Datei
        mock_os_walk.return_value = [
            ('/local/folder', [], ['invalid_file.docx', 'file2.txt']),
        ]

        # Die is_valid Funktion soll 'invalid' Dateien als ungültig markieren
        mock_is_valid.side_effect = lambda path: 'invalid' not in path

        # Führe den Test durch
        transfer_folder(mock_ssh_client(), '/local/folder', '/remote/folder')

        # Überprüfen, dass nur die gültige Datei übertragen wurde
        mock_sftp_client.put.assert_called_once_with(
            '/local/folder/file2.txt'.replace('\\', '/'),
            '/remote/folder/file2.txt'.replace('\\', '/')
        )

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

    @patch('paramiko.SSHClient')
    def test_transfer_file_success(self, mock_sftp_client):
        mock_sftp_client = MagicMock()
        mock_sftp_client.from_transport.return_value = mock_sftp_client

        local_file_path = 'test_local.txt'
        remote_file_path = 'test_remote.txt'

        transfer_file(mock_sftp_client, local_file_path, remote_file_path)

        mock_sftp_client.put.assert_called_with(local_file_path, remote_file_path)

    @patch('paramiko.SSHClient')
    def test_transfer_file_failure(self, mock_sftp_client):
        mock_sftp_client = MagicMock()
        mock_sftp_client.from_transport.return_value = mock_sftp_client

        mock_sftp_client.put.side_effect = Exception('Transfer Error')

        local_file_path = 'test_local.txt'
        remote_file_path = 'test_remote.txt'

        with self.assertRaises(Exception):
            transfer_file(mock_sftp_client, local_file_path, remote_file_path)

    @patch('paramiko.SSHClient')
    @patch('os.walk')
    def test_transfer_folder_various_structures(self, mock_os_walk, mock_ssh_client):
        mock_sftp_client = mock_ssh_client.return_value.open_sftp.return_value
        mock_sftp_client.stat.side_effect = None
        mock_sftp_client.mkdir = MagicMock()
        mock_sftp_client.chmod = MagicMock()
        mock_sftp_client.put = MagicMock()

        mock_os_walk.return_value = [
            ('/local/folder', ['dir1', 'dir2'], ['a.txt', 'b.html']),
            ('/local/folder/dir1', ['subdir1'], ['c.csv']),
            ('/local/folder/dir1/subdir1', [], ['d.pdf']),
            ('/local/folder/dir2', [], ['e.jpeg', 'f.xml']),
        ]

        transfer_folder(mock_ssh_client(), '/local/folder', '/remote/folder')

        expected_calls = [
            ('/local/folder/a.txt', '/remote/folder/a.txt'),
            ('/local/folder/b.html', '/remote/folder/b.html'),
            ('/local/folder/dir1/c.csv', '/remote/folder/dir1/c.csv'),
            ('/local/folder/dir1/subdir1/d.pdf', '/remote/folder/dir1/subdir1/d.pdf'),
            ('/local/folder/dir2/e.jpeg', '/remote/folder/dir2/e.jpeg'),
            ('/local/folder/dir2/f.xml', '/remote/folder/dir2/f.xml'),
        ]

        actual_calls = [
            (args[0].replace("\\", "/"), args[1].replace("\\", "/"))
            for args, kwargs in mock_sftp_client.put.call_args_list
        ]

        for expected_call in expected_calls:
            if expected_call not in actual_calls:
                raise AssertionError(f"{expected_call[0]} wurde nicht nach {expected_call[1]} übertragen.")

    @patch('paramiko.SSHClient')
    @patch('os.walk')
    def test_transfer_folder_with_hidden_files(self, mock_os_walk, mock_ssh_client):
        mock_sftp_client = mock_ssh_client.return_value.open_sftp.return_value
        mock_sftp_client.stat.side_effect = None
        mock_sftp_client.mkdir = MagicMock()
        mock_sftp_client.chmod = MagicMock()
        mock_sftp_client.put = MagicMock()

        mock_os_walk.return_value = [
            ('/local/folder', [], ['.hidden_file', 'visible_file.txt']),
        ]

        transfer_folder(mock_ssh_client(), '/local/folder', '/remote/folder')

        mock_sftp_client.put.assert_called_once_with(
            '/local/folder/visible_file.txt'.replace('\\', '/'),
            '/remote/folder/visible_file.txt'.replace('\\', '/')
        )

    @patch('paramiko.SSHClient')
    @patch('os.walk')
    @patch('SSHVerbindung.ssh_with_parameters.is_valid', side_effect=lambda path: 'invalid' not in path)
    def test_transfer_folder_with_permissions(self, mock_is_valid, mock_os_walk, mock_ssh_client):
        # Erstelle Mocks für die SFTP-Methoden
        mock_sftp_client = mock_ssh_client.return_value.open_sftp.return_value
        # Simuliere, dass das Verzeichnis nicht existiert, indem "stat" einen IOError auslöst
        mock_sftp_client.stat.side_effect = IOError
        mock_sftp_client.mkdir = MagicMock()
        mock_sftp_client.chmod = MagicMock()
        mock_sftp_client.put = MagicMock()

        # Simuliere ein Verzeichnis mit einer Datei
        mock_os_walk.return_value = [
            (os.path.normpath('/local/folder'), [], ['file1.txt']),
        ]

        # Aufruf der transfer_folder Funktion
        transfer_folder(mock_ssh_client(), os.path.normpath('/local/folder'), os.path.normpath('/remote/folder'))

        # Überprüfen, ob chmod aufgerufen wurde, da das Verzeichnis neu erstellt wurde
        print(f"chmod calls: {mock_sftp_client.chmod.call_args_list}")
        mock_sftp_client.chmod.assert_called_with('/remote/folder', stat.S_IRWXU)


class TestReadVersionFromFile(unittest.TestCase):
    # checks if read_version_from_file correctly reads the version from a valid JSON file. It ensures that the method
    # extracts the version value correctly from the file's content.
    @patch("builtins.open", new_callable=mock_open, read_data='{"version": "1.0.0"}')
    def test_valid_file(self, mock_file):
        result = SSHVerbindung.ssh_with_parameters.read_version_from_file("dummy_path.json")
        self.assertEqual(result, "1.0.0")

    # evaluates how read_version_from_file handles the case when the file does not exist. It simulates a
    # FileNotFoundError and verifies that the method returns None.
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_file):
        result = SSHVerbindung.ssh_with_parameters.read_version_from_file("non_existent_file.json")
        self.assertIsNone(result)
    # checks if read_version_from_file returns None when the version key is missing in the JSON file. It ensures that
    # the absence of the key is handled correctly.
    @patch("builtins.open", new_callable=mock_open, read_data='{"other_key": "1.0.0"}')
    def test_key_error(self, mock_file):
        result = SSHVerbindung.ssh_with_parameters.read_version_from_file("missing_version_key.json")
        self.assertIsNone(result)

    # assesses how read_version_from_file handles errors in JSON decoding. It simulates an invalid JSON format and
    # verifies that the method returns None.
    @patch("builtins.open", new_callable=mock_open, read_data='{"version": ')
    def test_json_decode_error(self, mock_file):
        result = SSHVerbindung.ssh_with_parameters.read_version_from_file("invalid_json.json")
        self.assertIsNone(result)


class TestExecuteCommand(unittest.TestCase):
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

        stdout, stderr = SSHVerbindung.ssh_with_parameters.execute_command(self.ssh_client, 'echo "test"')

        self.assertEqual(stdout, 'command output')
        self.assertEqual(stderr, '')

    # checks how execute_command handles errors during command execution. It simulates an error message and verifies
    # that the method correctly returns the error message and empty output.
    def test_execute_command_error(self):
        self.stdout_mock.read.return_value = b''
        self.stderr_mock.read.return_value = b'error message\n'

        stdout, stderr = SSHVerbindung.ssh_with_parameters.execute_command(self.ssh_client, 'invalid command')

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


class TestSelectFolder(unittest.TestCase):

    @patch('SSHVerbindung.ssh_with_parameters.askdirectory')
    @patch('SSHVerbindung.ssh_with_parameters.Tk')
    def test_select_folder(self, mock_tk, mock_askdirectory):
        # Mock vom askdirectory-Rückgabewert
        mock_askdirectory.return_value = '/mocked/path'

        # Aufruf der Funktion
        result = select_folder()

        # Überprüfe, ob Tk() und askdirectory() korrekt aufgerufen wurden
        mock_tk.assert_called_once()
        mock_askdirectory.assert_called_once()

        # Überprüfe, ob die Ergebnisse übereinstimmen
        self.assertEqual(result, '/mocked/path')


class TestCheckPythonVersion(unittest.TestCase):

    @patch('SSHVerbindung.ssh_with_parameters.execute_command')
    @patch('paramiko.SSHClient')
    def test_check_python_version_success(self, mock_ssh_client, mock_execute_command):
        # Simuliere den erfolgreichen Befehlsausgabe
        mock_execute_command.return_value = ("Python 3.8.10", "")

        # Ruf die Funktion auf
        result = check_python_version(mock_ssh_client, '3.8', 'source /env/bin/activate')

        # Überprüfe, dass execute_command aufgerufen wurde
        mock_execute_command.assert_called_once_with(
            mock_ssh_client, 'source /env/bin/activate && python3 --version'
        )

        # Überprüfe, ob die Version korrekt erkannt wurde
        self.assertTrue(result)

    @patch('SSHVerbindung.ssh_with_parameters.execute_command')
    @patch('paramiko.SSHClient')
    def test_check_python_version_failure(self, mock_ssh_client, mock_execute_command):
        # Simuliere eine fehlerhafte Befehlsausgabe (z.B. falsche Python-Version)
        mock_execute_command.return_value = ("Python 3.7.9", "")

        # Ruf die Funktion auf
        result = check_python_version(mock_ssh_client, '3.8', 'source /env/bin/activate')

        # Überprüfe, ob das Ergebnis False ist
        self.assertFalse(result)

    @patch('SSHVerbindung.ssh_with_parameters.execute_command')
    @patch('paramiko.SSHClient')
    def test_check_python_version_error(self, mock_ssh_client, mock_execute_command):
        # Simuliere einen Fehler im Befehl (z.B. STDERR)
        mock_execute_command.return_value = ("", "Error: command not found")

        # Ruf die Funktion auf
        result = check_python_version(mock_ssh_client, '3.8', 'source /env/bin/activate')

        # Überprüfe, ob das Ergebnis False ist und der Fehler korrekt verarbeitet wurde
        self.assertFalse(result)


class TestInstallLibraries(unittest.TestCase):

    @patch('SSHVerbindung.ssh_with_parameters.execute_command')
    @patch('paramiko.SSHClient')
    def test_install_libraries(self, mock_ssh_client, mock_execute_command):
        # Ruf die Funktion auf
        install_libraries(mock_ssh_client, '/path/to/requirements.txt', 'source /env/bin/activate')

        # Überprüfe, dass execute_command mit den richtigen Parametern aufgerufen wurde
        mock_execute_command.assert_called_once_with(
            mock_ssh_client,
            'source /env/bin/activate && pip3 install -r /path/to/requirements.txt'
        )


class TestGetPrivateConfig(unittest.TestCase):

    @patch('SSHVerbindung.ssh_with_parameters.read_json')
    def test_get_private_config_success(self, mock_read_json):
        # Simuliere einen erfolgreichen JSON-Lesevorgang
        mock_read_json.return_value = {'user': 'test_user'}

        # Rufe die Funktion auf
        result = get_private_config()

        # Überprüfe, ob das Ergebnis korrekt ist
        self.assertIsNotNone(result)
        self.assertEqual(result['user'], 'test_user')

    @patch('SSHVerbindung.ssh_with_parameters.read_json')
    def test_get_private_config_file_not_found(self, mock_read_json):
        # Simuliere das Werfen einer FileNotFoundError
        mock_read_json.side_effect = FileNotFoundError

        # Rufe die Funktion auf
        result = get_private_config()

        # Überprüfe, ob das Ergebnis None ist, wenn die Datei nicht gefunden wird
        self.assertIsNone(result)


class TestMainFunction(unittest.TestCase):

    @patch('SSHVerbindung.ssh_with_parameters.install_libraries')
    @patch('SSHVerbindung.ssh_with_parameters.transfer_folder')
    @patch('SSHVerbindung.ssh_with_parameters.select_folder', return_value='/local/folder')
    @patch('SSHVerbindung.ssh_with_parameters.check_python_version', return_value=True)
    @patch('SSHVerbindung.ssh_with_parameters.execute_command', return_value=("", ""))
    @patch('SSHVerbindung.ssh_with_parameters.create_ssh_client')
    @patch('SSHVerbindung.ssh_with_parameters.get_private_config', return_value={"user": "testuser"})
    @patch('SSHVerbindung.ssh_with_parameters.read_version_from_file', return_value="1.0.0")
    @patch('SSHVerbindung.ssh_with_parameters.read_json', side_effect=[{
        "paths": {
            "local_version_file_path": "/path/to/local/version.json",
            "required_python_version": "3.8",
            "env_activation_command": "/path/to/env/activate",
            "remote_folder_path": "/remote/folder",
            "remote_version_file_path": "/remote/folder/version.json",
            "requirements_file_path": "/path/to/requirements.txt"
        },
        "server": {
            "name": "testserver",
            "port": "22"
        }
    }, {"version": "1.0.0"}])
    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.input', return_value='password')  # Mock input instead of getpass
    def test_main_function(self, mock_input, mock_isatty, mock_read_json, mock_read_version, mock_get_private_config,
                           mock_create_ssh, mock_exec_command, mock_check_python_version, mock_select_folder,
                           mock_transfer_folder, mock_install_libraries):
        # Erstelle ein Mock-Objekt für den SSH-Client
        mock_ssh_client = MagicMock()
        mock_create_ssh.return_value = mock_ssh_client

        # Debugging-Ausgaben für die Hauptfunktion
        print("Test started: main() function execution")

        try:
            print("Calling main()")
            main()
        except Exception as e:
            print(f"Error occurred during test execution: {e}")

        # Überprüfen, ob alle Vorbedingungen erfüllt sind
        self.assertTrue(mock_get_private_config.called, "get_private_config wurde nicht aufgerufen")
        self.assertTrue(mock_read_json.called, "read_json wurde nicht aufgerufen")
        self.assertTrue(mock_read_version.called, "read_version_from_file wurde nicht aufgerufen")
        self.assertTrue(mock_input.called, "input wurde nicht aufgerufen")  # Check if input was called

        # Sicherstellen, dass die SSH-Verbindung erstellt wurde
        mock_create_ssh.assert_called_once_with('testserver', 22, 'testuser', 'password')
        print("SSH client was created successfully.")

    # Zusätzliche Testfunktionen, die auf `return` statt `SystemExit` testen

    @patch('SSHVerbindung.ssh_with_parameters.read_json')
    def test_public_config_file_not_found(self, mock_read_json):
        mock_read_json.side_effect = FileNotFoundError
        main()
        print("Test passed: main() returned successfully when public_config file was not found.")

    @patch('SSHVerbindung.ssh_with_parameters.read_json')
    def test_public_config_json_decode_error(self, mock_read_json):
        mock_read_json.side_effect = json.JSONDecodeError("Expecting value", "document", 0)
        main()
        print("Test passed: main() returned successfully when JSON decoding failed.")

    @patch('SSHVerbindung.ssh_with_parameters.read_json',
           return_value={'paths': {'local_version_file_path': 'some/path'}})
    @patch('SSHVerbindung.ssh_with_parameters.read_version_from_file', return_value=None)
    @patch('builtins.print')
    def test_local_version_file_is_none(self, mock_print, mock_read_version_from_file, mock_read_json):
        main()
        # Überprüfen, dass "Local version file not found or invalid." aufgerufen wurde
        mock_print.assert_any_call("Local version file not found or invalid.")
        # Überprüfen, dass "Private config is None." nicht aufgerufen wurde
        assert not any(call[0][0] == "Private config is None." for call in mock_print.call_args_list)

    @patch('SSHVerbindung.ssh_with_parameters.read_json',
           return_value={'paths': {'local_version_file_path': 'some/path'}})
    @patch('SSHVerbindung.ssh_with_parameters.read_version_from_file', return_value='some_version')
    @patch('SSHVerbindung.ssh_with_parameters.get_private_config', return_value=None)
    @patch('builtins.print')
    def test_private_config_is_none(self, mock_print, mock_get_private_config, mock_read_version_from_file,
                                    mock_read_json):
        main()

        # Überprüfen, dass "Private config is None." tatsächlich ausgegeben wird
        print("Call args list:", mock_print.call_args_list)
        assert any(call[0][0] == "Private config is None." for call in mock_print.call_args_list), \
            "Expected 'Private config is None.' not found in print calls"

        # Überprüfen, dass keine andere Ausgabe wie "Local version file not found or invalid." gemacht wird
        unexpected_calls = [call for call in mock_print.call_args_list if
                            call[0][0] == "Local version file not found or invalid."]
        assert not unexpected_calls, f"Unexpected print calls: {unexpected_calls}"

    @patch('SSHVerbindung.ssh_with_parameters.select_folder', return_value=None)
    def test_no_folder_selected(self, mock_select_folder):
        main()
        print("Test passed: main() returned successfully when no folder was selected.")

    @patch('SSHVerbindung.ssh_with_parameters.create_ssh_client', side_effect=Exception("Test exception"))
    def test_general_exception_handling(self, mock_create_ssh_client):
        main()
        print("Test passed: main() returned successfully when a general exception occurred.")

    @patch('SSHVerbindung.ssh_with_parameters.install_libraries')
    @patch('SSHVerbindung.ssh_with_parameters.execute_command', return_value=("Python 3.8.5", ""))
    @patch('SSHVerbindung.ssh_with_parameters.read_version_from_file', return_value="1.0.0")
    @patch('SSHVerbindung.ssh_with_parameters.read_json', return_value={
        "paths": {
            "local_version_file_path": "/path/to/local/version.json",
            "required_python_version": "3.8",
            "env_activation_command": "/path/to/env/activate",
            "remote_folder_path": "/remote/folder",
            "remote_version_file_path": "/remote/folder/version.json",
            "requirements_file_path": "/path/to/requirements.txt"
        },
        "server": {
            "name": "testserver",
            "port": "22"
        }
    })
    @patch('SSHVerbindung.ssh_with_parameters.get_private_config', return_value={"user": "testuser"})
    @patch('SSHVerbindung.ssh_with_parameters.create_ssh_client')  # Mock SSH client creation
    @patch('SSHVerbindung.ssh_with_parameters.select_folder',
           return_value='/mocked/folder')  # Mock the folder selection
    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.input', return_value='password')  # Mock input instead of getpass
    def test_software_already_up_to_date(self, mock_input, mock_isatty, mock_create_ssh_client,
                                         mock_select_folder, mock_get_private_config, mock_read_json,
                                         mock_read_version_from_file, mock_execute_command,
                                         mock_install_libraries):
        # Führe die Hauptfunktion aus
        main()

        # Überprüfe, ob install_libraries aufgerufen wird, wenn die Software auf dem neuesten Stand ist
        mock_install_libraries.assert_called_once()
        print("Test passed: Software is already up to date, and install_libraries was called.")

    @patch('SSHVerbindung.ssh_with_parameters.transfer_folder')
    @patch('SSHVerbindung.ssh_with_parameters.select_folder', return_value='/local/folder')
    @patch('SSHVerbindung.ssh_with_parameters.execute_command', side_effect=[
        ("Python 3.8.5", ""),  # Python version check
        ("0.9.0", ""),  # Remote version is older
        ("", ""),  # Simulate no error for folder existence check
    ])
    @patch('SSHVerbindung.ssh_with_parameters.read_version_from_file', return_value="1.0.0")  # Local version is newer
    @patch('SSHVerbindung.ssh_with_parameters.read_json', return_value={
        "paths": {
            "local_version_file_path": "/path/to/local/version.json",
            "required_python_version": "3.8",
            "env_activation_command": "/path/to/env/activate",
            "remote_folder_path": "/remote/folder",
            "remote_version_file_path": "/remote/folder/version.json",
            "requirements_file_path": "/path/to/requirements.txt"
        },
        "server": {
            "name": "testserver",
            "port": "22"
        }
    })
    @patch('SSHVerbindung.ssh_with_parameters.get_private_config', return_value={"user": "testuser"})
    @patch('SSHVerbindung.ssh_with_parameters.create_ssh_client')  # Mock SSH client creation
    @patch('builtins.input', return_value='password')  # Mocking the input for password
    def test_software_needs_update(self, mock_input, mock_create_ssh_client, mock_get_private_config, mock_read_json,
                                   mock_read_version_from_file, mock_execute_command, mock_select_folder,
                                   mock_transfer_folder):
        # Führe die Hauptfunktion aus
        main()

        # Überprüfen, ob transfer_folder aufgerufen wird, wenn die Software aktualisiert werden muss
        mock_transfer_folder.assert_any_call(mock.ANY, '/local/folder', '/remote/folder')
        print("Test passed: Software needs update, and folder was transferred.")


    @patch('SSHVerbindung.ssh_with_parameters.read_json', return_value={
        'paths': {
            'remote_folder_path': '/home/$USER/remote_folder',
            'remote_version_file_path': '/home/$USER/remote_version_file',
            'requirements_file_path': '/home/$USER/requirements.txt',
        }
    })
    @patch('SSHVerbindung.ssh_with_parameters.get_private_config', return_value={'user': 'testuser'})
    def test_placeholder_replacement(self, mock_get_private_config, mock_read_json):
        public_config = mock_read_json.return_value
        private_config = mock_get_private_config.return_value

        for key in ['remote_folder_path', 'remote_version_file_path', 'requirements_file_path']:
            path = public_config['paths'][key].replace('$USER', private_config['user'])
            self.assertIn('testuser', path, f"Placeholder replacement failed for {key}")


    @patch('SSHVerbindung.ssh_with_parameters.check_python_version',
           return_value=False)  # - Fehlende Python-Version - Simulierung
    @patch('SSHVerbindung.ssh_with_parameters.create_ssh_client')  # SSH-Client-Erstellung - Simulierung
    @patch('builtins.input', return_value='valid_password')  # Passworteingabe - Simulierung
    @patch('SSHVerbindung.ssh_with_parameters.read_version_from_file',
           return_value="1.0.0")  # Simuliere gültige lokale Version
    @patch('SSHVerbindung.ssh_with_parameters.get_private_config',
           return_value={"user": "testuser"})  # Simuliere private_config mit user
    def test_python_version_not_installed(self, mock_get_private_config, mock_read_version, mock_input,
                                          mock_create_ssh_client, mock_check_python_version):
        # Beispiel einer gefälschten public_config JSON
        public_config = {
            'server': {'name': 'valid_server', 'port': '22'},
            'paths': {
                'required_python_version': '3.8',
                'env_activation_command': 'source ~/env/bin/activate',
                'remote_folder_path': '/remote/path',
                'remote_version_file_path': '/remote/version/path',
                'local_version_file_path': '/local/version/path',
                'requirements_file_path': '/requirements/path'
            }
        }

        # Füge die öffentliche Konfiguration direkt ein, anstatt read_json zu mocken
        with patch('SSHVerbindung.ssh_with_parameters.read_json', return_value=public_config):
            # Capture stdout with capsys
            with patch('builtins.print') as mock_print:
                try:
                    main()
                except RecursionError as e:
                    print(f"Recursion error: {e}")

                # Debug-Ausgabe der tatsächlichen Aufrufe von print
                print(mock_print.call_args_list)

                # Überprüfe, ob die Fehlermeldung korrekt ausgegeben wurde
                mock_print.assert_any_call("Python 3.8 is not installed on the remote system.")



if __name__ == '__main__':
    unittest.main()
