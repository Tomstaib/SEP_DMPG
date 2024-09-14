import os
import subprocess
import sys
from io import StringIO
import unittest
from unittest.mock import patch, mock_open, MagicMock
import paramiko

# Lokale Module
from generate_ssh_key import generate_ssh_key, send_public_key_to_server, main

# Schlüssel- und Server-Informationen
KEY_PATH = os.path.expanduser("~/.ssh/id_rsa_tunnel_to_server")
REMOTE_HOST = "imt-sep-001.lin.hs-osnabrueck.de"
REMOTE_USER = "sep"
REMOTE_KEY_PATH = f"/home/{REMOTE_USER}/.ssh/authorized_keys"
COMMENT = "distributed_server@sep"
PASSPHRASE = ""


class TestGenerateSSHKey(unittest.TestCase):
    """
    Testet die Funktionalität zur SSH-Schlüsselgenerierung.
    Diese Tests prüfen, ob der Schlüssel korrekt erstellt wird,
    was für eine sichere Kommunikation unerlässlich ist.
    """

    @patch("subprocess.run")
    @patch("os.makedirs")
    def test_generate_ssh_key_success(self, mock_makedirs, mock_subprocess):
        """Testet die erfolgreiche SSH-Schlüsselgenerierung."""
        result = generate_ssh_key(KEY_PATH, COMMENT, PASSPHRASE)
        mock_makedirs.assert_called_once_with(os.path.dirname(KEY_PATH), exist_ok=True)
        mock_subprocess.assert_called_once_with(
            ['ssh-keygen', '-t', 'rsa', '-b', '4096', '-f', KEY_PATH, '-C', COMMENT, '-N', PASSPHRASE],
            check=True
        )
        self.assertTrue(result)

    @patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, 'ssh-keygen'))
    def test_generate_ssh_key_failure(self, mock_subprocess):
        """Testet die Fehlerbehandlung, wenn die Schlüsselgenerierung fehlschlägt."""
        result = generate_ssh_key(KEY_PATH, COMMENT, PASSPHRASE)
        mock_subprocess.assert_called_once()
        self.assertFalse(result)

    @patch("os.path.exists", return_value=False)
    @patch("generate_ssh_key.generate_ssh_key", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="mocked_public_key")
    @patch("paramiko.SSHClient", autospec=True)
    def test_generate_ssh_key_if_not_exists(self, MockSSHClient, mock_open, mock_generate_ssh_key, mock_exists):
        """Testet, ob der SSH-Schlüssel generiert wird, wenn er nicht existiert."""
        mock_ssh_instance = MockSSHClient.return_value
        main(ssh_client=mock_ssh_instance, remote_password="mock_password")
        mock_generate_ssh_key.assert_called_once_with(KEY_PATH, COMMENT, PASSPHRASE)
        mock_ssh_instance.connect.assert_called_once_with(REMOTE_HOST, username=REMOTE_USER, password="mock_password")

    @patch("os.path.exists", return_value=False)
    @patch("generate_ssh_key.generate_ssh_key", return_value=False)
    @patch("builtins.open", new_callable=mock_open, read_data="mocked_public_key")
    @patch("paramiko.SSHClient", autospec=True)
    def test_generate_ssh_key_failure_returns(self, MockSSHClient, mock_open, mock_generate_ssh_key, mock_exists):
        """Testet, dass die Funktion bei Fehlschlagen der Schlüsselgenerierung korrekt beendet wird."""
        mock_ssh_instance = MockSSHClient.return_value
        captured_output = StringIO()
        sys.stdout = captured_output
        main(ssh_client=mock_ssh_instance, remote_password="mock_password")
        sys.stdout = sys.__stdout__
        mock_generate_ssh_key.assert_called_once_with(KEY_PATH, COMMENT, PASSPHRASE)
        mock_ssh_instance.connect.assert_not_called()
        self.assertNotIn("Password input received", captured_output.getvalue())


class TestSSHConnection(unittest.TestCase):
    """
    Testet die SSH-Verbindung unter verschiedenen Bedingungen.
    Diese Tests prüfen, ob eine Verbindung ohne Probleme hergestellt werden kann,
    was für die Kommunikation zwischen Client und Server unerlässlich ist.
    """

    @patch("paramiko.SSHClient", autospec=True)
    @patch("builtins.open", new_callable=mock_open, read_data="mocked_public_key")
    @patch("os.path.exists", return_value=True)
    def test_ssh_connection_without_interactive_password(self, mock_exists, mock_open, MockSSHClient):
        """Testet die SSH-Verbindung ohne interaktive Passworteingabe."""
        mock_ssh_instance = MockSSHClient.return_value
        mock_ssh_instance.connect = MagicMock()
        main(ssh_client=mock_ssh_instance, remote_password="mock_password")
        mock_ssh_instance.connect.assert_called_once_with(REMOTE_HOST, username=REMOTE_USER, password="mock_password")

    @patch("paramiko.SSHClient", autospec=True)
    @patch("builtins.open", new_callable=mock_open, read_data="mocked_public_key")
    @patch("os.path.exists", return_value=True)
    @patch("getpass.getpass", return_value="mock_password")
    def test_ssh_connection_close_called(self, mock_getpass, mock_exists, mock_open, MockSSHClient):
        """Testet, ob die SSH-Verbindung korrekt geschlossen wird."""
        mock_ssh_instance = MockSSHClient.return_value
        main(ssh_client=mock_ssh_instance, remote_password="mock_password")
        mock_ssh_instance.close.assert_called_once()

    @patch("os.path.exists", return_value=True)
    @patch("generate_ssh_key.send_public_key_to_server", return_value=False)
    @patch("builtins.open", new_callable=mock_open, read_data="mocked_public_key")
    @patch("paramiko.SSHClient", autospec=True)
    def test_send_public_key_failure_returns(self, MockSSHClient, mock_open, mock_send_public_key, mock_exists):
        """Testet, dass die Funktion bei einem Fehler beim Senden des öffentlichen Schlüssels korrekt beendet wird."""
        mock_ssh_instance = MockSSHClient.return_value
        captured_output = StringIO()
        sys.stdout = captured_output
        main(ssh_client=mock_ssh_instance, remote_password="mock_password")
        sys.stdout = sys.__stdout__
        mock_send_public_key.assert_called_once_with(mock_ssh_instance, "mocked_public_key", REMOTE_USER, REMOTE_HOST, REMOTE_KEY_PATH)
        self.assertEqual(mock_ssh_instance.connect.call_count, 1)


class TestSendPublicKeyToServer(unittest.TestCase):
    """
    Testet das Senden des öffentlichen Schlüssels an den Server.
    Diese Tests stellen sicher, dass der Schlüssel erfolgreich zum Server hinzugefügt wird,
    was die Grundlage für eine sichere Authentifizierung ist.
    """

    @patch("paramiko.SSHClient")
    def test_send_public_key_success(self, mock_ssh_client):
        """Testet das erfolgreiche Hinzufügen des öffentlichen Schlüssels auf dem Server."""
        mock_sftp_client = MagicMock()
        mock_file = MagicMock()
        mock_sftp_client.open.return_value.__enter__.return_value = mock_file
        mock_ssh_client_instance = mock_ssh_client.return_value
        mock_ssh_client_instance.open_sftp.return_value = mock_sftp_client
        public_key = "ssh-rsa AAAAB3Nza...mocked_key"
        result = send_public_key_to_server(mock_ssh_client_instance, public_key, REMOTE_USER, REMOTE_HOST, REMOTE_KEY_PATH)
        mock_sftp_client.open.assert_called_once_with(REMOTE_KEY_PATH, 'a')
        mock_file.write.assert_called_once_with(public_key + "\n")
        self.assertTrue(result)

    @patch("paramiko.SSHClient")
    def test_send_public_key_create_ssh_directory(self, mock_ssh_client):
        """Testet die Erstellung des SSH-Verzeichnisses auf dem Server."""
        mock_sftp_client = MagicMock()
        mock_sftp_client.chdir.side_effect = IOError
        mock_ssh_client_instance = mock_ssh_client.return_value
        mock_ssh_client_instance.open_sftp.return_value = mock_sftp_client
        mock_file = MagicMock()
        mock_sftp_client.open.return_value.__enter__.return_value = mock_file
        public_key = "ssh-rsa AAAAB3Nza...mocked_key"
        result = send_public_key_to_server(mock_ssh_client_instance, public_key, REMOTE_USER, REMOTE_HOST, REMOTE_KEY_PATH)
        mock_sftp_client.mkdir.assert_called_once_with('.ssh')
        mock_sftp_client.chmod.assert_called_once_with('.ssh', 0o700)
        mock_sftp_client.open.assert_called_once_with(REMOTE_KEY_PATH, 'a')
        mock_file.write.assert_called_once_with(public_key + "\n")
        self.assertTrue(result)

    @patch("paramiko.SSHClient")
    def test_send_public_key_open_failure(self, mock_ssh_client):
        """Testet den Fehlerfall beim Öffnen der Datei authorized_keys auf dem Server."""
        mock_sftp_client = MagicMock()
        mock_sftp_client.open.side_effect = IOError("Open failed")
        mock_ssh_client_instance = mock_ssh_client.return_value
        mock_ssh_client_instance.open_sftp.return_value = mock_sftp_client
        public_key = "ssh-rsa AAAAB3Nza...mocked_key"
        result = send_public_key_to_server(mock_ssh_client_instance, public_key, REMOTE_USER, REMOTE_HOST, REMOTE_KEY_PATH)
        mock_sftp_client.open.assert_called_once_with(REMOTE_KEY_PATH, 'a')
        self.assertFalse(result)

    @patch("paramiko.SSHClient")
    def test_send_public_key_connection_failure(self, mock_ssh_client):
        """Testet den Fehlerfall bei Verbindungsproblemen zum Server."""
        mock_ssh_client_instance = mock_ssh_client.return_value
        mock_ssh_client_instance.open_sftp.side_effect = paramiko.SSHException("Connection failed")
        public_key = "ssh-rsa AAAAB3Nza...mocked_key"
        result = send_public_key_to_server(mock_ssh_client_instance, public_key, REMOTE_USER, REMOTE_HOST, REMOTE_KEY_PATH)
        mock_ssh_client_instance.open_sftp.assert_called_once()
        self.assertFalse(result)



class TestReadSSHKey(unittest.TestCase):
    """
    Testet das Lesen des öffentlichen Schlüssels, um sicherzustellen,
    dass dieser korrekt geladen und versendet werden kann.
    """

    @patch('sys.stdin', new_callable=StringIO)
    @patch("builtins.open", new_callable=mock_open, read_data="mocked_public_key")
    @patch("os.path.exists", return_value=True)
    def test_read_public_key_success(self, mock_exists, mock_open, mock_stdin):
        """Testet das erfolgreiche Lesen des öffentlichen Schlüssels."""
        mock_stdin.write('some input\n')
        mock_stdin.seek(0)
        main()
        mock_open.assert_called_once_with(f"{KEY_PATH}.pub", "r")

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("os.path.exists", return_value=True)
    def test_read_public_key_file_not_found(self, mock_exists, mock_open):
        """Testet den Fehlerfall, wenn die öffentliche Schlüsseldatei nicht existiert."""
        captured_output = StringIO()
        sys.stdout = captured_output
        main()
        sys.stdout = sys.__stdout__
        self.assertIn("Error reading public key", captured_output.getvalue())


class TestMainFunction(unittest.TestCase):
    """
    Testet die Main-Funktion, die die Logik zur SSH-Schlüsselgenerierung,
    dem Senden des Schlüssels und dem Verbindungsaufbau zum Server umfasst.
    """

    @patch("sys.stdin.isatty", return_value=True)
    @patch("os.path.exists", return_value=False)
    @patch("subprocess.run", return_value=None)
    @patch("generate_ssh_key.getpass", return_value="mock_password")
    @patch("paramiko.SSHClient.connect", side_effect=paramiko.SSHException("Connection failed"))
    @patch("builtins.open", new_callable=mock_open, read_data="mocked_public_key")
    def test_main_connection_failure(self, mock_open, mock_connect, mock_getpass, mock_run, mock_exists, mock_isatty):
        """Testet die Main-Funktion bei Verbindungsproblemen."""
        main()
        mock_run.assert_called_once()
        mock_connect.assert_called_once_with(REMOTE_HOST, username=REMOTE_USER, password="mock_password")

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("os.path.exists", return_value=True)
    @patch("paramiko.SSHClient")
    def test_main_public_key_file_not_found(self, mock_ssh_client, mock_exists, mock_open):
        """Testet den Fehlerfall, wenn die Datei mit dem öffentlichen Schlüssel nicht gefunden wird."""
        captured_output = StringIO()
        sys.stdout = captured_output
        main()
        sys.stdout = sys.__stdout__
        self.assertIn("Error reading public key", captured_output.getvalue())


if __name__ == "__main__":
    unittest.main()
