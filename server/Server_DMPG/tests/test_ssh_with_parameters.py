import unittest
from unittest.mock import patch, MagicMock, mock_open
import paramiko
import os
import json
import sys
import builtins

from src.util import ssh_with_parameters


class TestSSHWithParameters(unittest.TestCase):

    @patch('paramiko.SSHClient')
    def test_create_ssh_client(self, MockSSHClient):
        mock_client = MagicMock()
        MockSSHClient.return_value = mock_client

        client = ssh_with_parameters.create_ssh_client('server', 22, 'user', 'password')

        MockSSHClient.assert_called_once()
        mock_client.load_system_host_keys.assert_called_once()
        # Compare type instead of instance
        self.assertTrue(isinstance(mock_client.set_missing_host_key_policy.call_args[0][0], paramiko.AutoAddPolicy))
        mock_client.connect.assert_called_once_with('server', 22, 'user', 'password')

    @patch('paramiko.SSHClient')
    def test_transfer_folder(self, MockSSHClient):
        mock_ssh = MagicMock()
        mock_sftp = MagicMock()
        mock_ssh.open_sftp.return_value = mock_sftp
        mock_sftp.stat.side_effect = IOError

        ssh_with_parameters.transfer_folder(mock_ssh, 'local_folder', 'remote_folder')

        mock_sftp.mkdir.assert_called()
        mock_sftp.chmod.assert_called()

    @patch('builtins.open', new_callable=mock_open, read_data='{"version": "1.0.0"}')
    def test_read_version_from_file(self, mock_open):
        version = ssh_with_parameters.read_version_from_file('version.json')
        self.assertEqual(version, '1.0.0')

    @patch('paramiko.SSHClient')
    def test_execute_command(self, MockSSHClient):
        mock_ssh = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.read.return_value = b'output'
        mock_stderr.read.return_value = b'error'
        mock_ssh.exec_command.return_value = (None, mock_stdout, mock_stderr)

        stdout, stderr = ssh_with_parameters.execute_command(mock_ssh, 'command')

        self.assertEqual(stdout, 'output')
        self.assertEqual(stderr, 'error')

    @patch('paramiko.SSHClient')
    def test_check_python_version(self, MockSSHClient):
        mock_ssh = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.read.return_value = b'Python 3.11.8'
        mock_stderr.read.return_value = b''
        mock_ssh.exec_command.return_value = (None, mock_stdout, mock_stderr)

        result = ssh_with_parameters.check_python_version(mock_ssh, '3.11.8', 'env_activation_command')
        self.assertTrue(result)

    @patch('paramiko.SSHClient')
    @patch('src.util.ssh_with_parameters.execute_command')
    def test_install_libraries(self, mock_execute_command, MockSSHClient):
        mock_ssh = MagicMock()
        requirements_file = 'requirements.txt'
        env_activation_command = 'activate_env'

        ssh_with_parameters.install_libraries(mock_ssh, requirements_file, env_activation_command)

        mock_execute_command.assert_called_once_with(
            mock_ssh,
            f'source {env_activation_command} && pip3 install -r {requirements_file}'
        )

    @patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
    @patch('os.path.isfile')
    @patch('os.path.dirname')
    def test_read_json(self, mock_dirname, mock_isfile, mock_open):
        mock_isfile.return_value = True
        mock_dirname.side_effect = lambda path: os.path.join(path, '..')

        data = ssh_with_parameters.read_json('config.json')

        self.assertEqual(data, {"key": "value"})

    @patch('builtins.input', side_effect=['password'])
    @patch('getpass.getpass', return_value='password')
    def test_main(self, mock_getpass, mock_input):
        mock_public_config = {
            'server': {'name': 'server', 'port': 22},
            'paths': {
                'local_version_file_path': 'local_version.json',
                'remote_folder_path': 'remote_folder',
                'remote_version_file_path': 'remote_version.json',
                'required_python_version': '3.8',
                'env_activation_command': 'env_activation_command',
                'requirements_file_path': 'requirements.txt'
            }
        }

        mock_private_config = {'user': 'user'}

        with patch('json.load', side_effect=[mock_public_config, mock_private_config]):
            with patch('os.path.isfile', return_value=True):
                with patch('builtins.open', new_callable=mock_open, read_data='{"version": "1.0.0"}'):
                    with patch('paramiko.SSHClient', MagicMock()):
                        ssh_with_parameters.main()


if __name__ == '__main__':
    unittest.main()
