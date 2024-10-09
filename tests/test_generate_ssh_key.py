import sys
import os
import unittest
import paramiko
import subprocess
from io import StringIO
from flask import Flask, session
from unittest.mock import patch, MagicMock

# Für Dockercontainer zum Initialisieren der lokalen Module
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Datenspeicherung/Python')
))

from generate_ssh_key import setup_ssh_connection, generate_ssh_key, send_public_key_to_server, close_ssh_connection, KEY_PATH


class TestSSHConnection(unittest.TestCase):
    """
    Testklasse für die SSH-Verbindung und Schlüsselgenerierung.
    Diese Tests simulieren verschiedene Situationen im SSH-Verbindungsprozess.
    """

    @patch('generate_ssh_key.paramiko.SSHClient')  # Mock für den SSH-Client
    @patch('generate_ssh_key.os.path.exists', return_value=True)  # Simuliere, dass der SSH-Schlüssel existiert
    @patch('builtins.print')  # Mock für den print-Aufruf
    def test_ssh_key_exists(self, mock_print, mock_path_exists, mock_ssh_client):
        """Test, der überprüft, ob eine SSH-Verbindung übersprungen wird, wenn der Schlüssel existiert."""
        username = "test_user"

        setup_ssh_connection(username, remote_password="mocked_password")

        mock_print.assert_any_call(f"SSH key already exists at {KEY_PATH}. Skipping key generation.")

        mock_ssh_client.assert_not_called()

    @patch('generate_ssh_key.os.path.exists', return_value=False)  # Simuliere, dass der SSH-Schlüssel nicht existiert
    @patch('generate_ssh_key.paramiko.SSHClient')  # Mock für den SSH-Client
    @patch('generate_ssh_key.generate_ssh_key')  # Mock für die Schlüsselerzeugung
    def test_authentication_exception_handling(self, mock_generate_ssh_key, mock_ssh_client, mock_path_exists):
        """Testet, wie die Funktion auf Authentifizierungsfehler reagiert."""
        mock_ssh_client_instance = MagicMock()
        mock_ssh_client.return_value = mock_ssh_client_instance

        mock_ssh_client_instance.connect.side_effect = paramiko.ssh_exception.AuthenticationException

        username = "test_user"
        remote_password = "mocked_password"

        setup_ssh_connection(username, remote_password=remote_password)

        mock_ssh_client_instance.close.assert_called_once()

    @patch('builtins.print')  # Mock für den print-Aufruf
    def test_close_ssh_connection_exception(self, mock_print):
        """Testet, ob Ausnahmen beim Schließen der SSH-Verbindung korrekt behandelt werden."""
        mock_ssh_client = MagicMock()
        mock_ssh_client.close.side_effect = Exception("Mocked exception")

        close_ssh_connection(mock_ssh_client)

        mock_print.assert_any_call("Error while closing SSH connection: Mocked exception")


class TestGenerateSSHKey(unittest.TestCase):
    """
    Testklasse für die SSH-Schlüsselerzeugung.
    Simuliert verschiedene Szenarien der Schlüsselerstellung.
    """

    @patch('generate_ssh_key.subprocess.run')  # Mock subprocess.run
    @patch('os.makedirs')  # Mock os.makedirs
    @patch('os.path.dirname', return_value="/mocked/ssh/dir")  # Mock os.path.dirname
    def test_generate_ssh_key(self, mock_dirname, mock_makedirs, mock_run):
        """Testet, ob ein SSH-Schlüssel erfolgreich generiert wird."""
        key_path = "/mocked/ssh/dir/id_rsa"
        comment = "test_comment"
        passphrase = "test_passphrase"

        generate_ssh_key(key_path, comment, passphrase)

        mock_dirname.assert_called_once_with(key_path)
        mock_makedirs.assert_called_once_with("/mocked/ssh/dir", exist_ok=True)

        # Überprüfen, ob subprocess.run korrekt aufgerufen wurde
        mock_run.assert_called_once_with([
            "ssh-keygen",
            "-t", "rsa",
            "-b", "4096",
            "-f", key_path,
            "-C", comment,
            "-N", passphrase
        ], check=True)


class TestSendPublicKeyToServerEdgeCase(unittest.TestCase):
    """
    Testklasse für das Senden des öffentlichen Schlüssels an den Server.
    Überprüft, wie die Funktion auf Fehler reagiert.
    """

    @patch('generate_ssh_key.paramiko.SSHClient')
    def test_send_public_key_to_server_ioerror(self, mock_ssh_client):
        """Testet, wie die Funktion auf E/A-Fehler reagiert."""
        mock_sftp = MagicMock()
        mock_ssh_client_instance = MagicMock()
        mock_ssh_client_instance.open_sftp.return_value = mock_sftp
        mock_ssh_client.return_value = mock_ssh_client_instance

        # Simuliere I/O-Fehler beim Zugriff auf das .ssh-Verzeichnis
        mock_sftp.chdir.side_effect = IOError

        # Testparameter
        public_key = "mocked_public_key"
        username = "test_user"
        remote_host = "hpc.hs-osnabrueck.de"
        remote_key_path = "/home/test_user/.ssh/authorized_keys"

        send_public_key_to_server(mock_ssh_client_instance, public_key, username, remote_host, remote_key_path)

        mock_sftp.mkdir.assert_called_once_with('.ssh')
        mock_sftp.chmod.assert_called_once_with('.ssh', 0o700)
        mock_sftp.open.assert_called_once_with(remote_key_path, 'a')
        mock_sftp.close.assert_called_once()


class TestSSHConnectionException(unittest.TestCase):
    """
    Testklasse für den generischen Ausnahmefall bei der SSH-Verbindung.
    """

    @patch('generate_ssh_key.paramiko.SSHClient')
    @patch('generate_ssh_key.paramiko.RSAKey')
    @patch('generate_ssh_key.os.path.exists', return_value=False)
    @patch('generate_ssh_key.generate_ssh_key')
    def test_ssh_connection_with_password(self, mock_generate_ssh_key, mock_path_exists, mock_rsa_key, mock_ssh_client):
        """Testet den Verbindungsaufbau mit Passwort."""
        mock_ssh_client_instance = mock_ssh_client.return_value
        mock_ssh_client_instance.connect = MagicMock()

        username = "test_user"
        remote_password = "mock_password"

        setup_ssh_connection(username, remote_password=remote_password)

        mock_ssh_client_instance.connect.assert_called_with(
            "hpc.hs-osnabrueck.de", username=username, password=remote_password
        )
        print("Test for password-based connection passed.")

    @patch('generate_ssh_key.paramiko.SSHClient')
    @patch('generate_ssh_key.paramiko.RSAKey')
    @patch('generate_ssh_key.os.path.exists', return_value=False)
    @patch('generate_ssh_key.generate_ssh_key')
    def test_ssh_connection_fallback_to_rsa(self, mock_generate_ssh_key, mock_path_exists, mock_rsa_key, mock_ssh_client):
        """Testet den Verbindungsaufbau mit RSA-Schlüssel, wenn kein Passwort vorhanden ist."""
        app = Flask(__name__)
        app.secret_key = 'test_secret_key'

        with app.test_request_context('/'):
            session['remote_password'] = None

            mock_ssh_client_instance = mock_ssh_client.return_value
            mock_ssh_client_instance.connect = MagicMock()

            mock_rsa_key_instance = mock_rsa_key.return_value

            username = "test_user"

            setup_ssh_connection(username)

            mock_ssh_client_instance.connect.assert_called_with(
                "hpc.hs-osnabrueck.de", username=username, pkey=mock_rsa_key_instance
            )
            print("Test for RSA key fallback passed.")


class TestSSHConnectionExceptionHandling(unittest.TestCase):
    """
    Testklasse für das generische Fehlerhandling bei der SSH-Verbindung.
    """

    @patch('generate_ssh_key.paramiko.SSHClient')
    @patch('generate_ssh_key.paramiko.RSAKey')
    @patch('generate_ssh_key.os.path.exists', return_value=False)
    @patch('generate_ssh_key.generate_ssh_key')
    def test_ssh_connection_generic_exception(self, mock_generate_ssh_key, mock_path_exists, mock_rsa_key, mock_ssh_client):
        """Testet, wie die Funktion auf allgemeine Verbindungsfehler reagiert."""
        app = Flask(__name__)
        app.secret_key = 'test_secret_key'

        with app.test_request_context('/'):
            mock_ssh_client_instance = mock_ssh_client.return_value
            mock_ssh_client_instance.connect.side_effect = Exception("Generic connection error")

            captured_output = StringIO()
            sys.stdout = captured_output

            username = "test_user"

            result = setup_ssh_connection(username)

            sys.stdout = sys.__stdout__
            self.assertIn("Error during SSH connection: Generic connection error", captured_output.getvalue())
            self.assertIsNone(result)


class TestSSHCloseConnection(unittest.TestCase):
    """
    Testklasse für das Schließen der SSH-Verbindung.
    """

    @patch('generate_ssh_key.paramiko.SSHClient')
    def test_close_ssh_connection_success(self, mock_ssh_client):
        """Testet, ob die SSH-Verbindung erfolgreich geschlossen wird."""
        app = Flask(__name__)
        app.secret_key = 'test_secret_key'

        with app.test_request_context('/'):
            mock_ssh_client_instance = mock_ssh_client.return_value
            mock_ssh_client_instance.close = MagicMock()

            captured_output = StringIO()
            sys.stdout = captured_output

            close_ssh_connection(mock_ssh_client_instance)

            mock_ssh_client_instance.close.assert_called_once()
            sys.stdout = sys.__stdout__
            self.assertIn("SSH connection closed.", captured_output.getvalue())

    @patch('generate_ssh_key.paramiko.SSHClient')
    def test_close_ssh_connection_no_client(self, mock_ssh_client):
        """Testet, dass keine Aktion durchgeführt wird, wenn kein SSH-Client existiert."""
        app = Flask(__name__)
        app.secret_key = 'test_secret_key'

        with app.test_request_context('/'):
            captured_output = StringIO()
            sys.stdout = captured_output

            close_ssh_connection(None)

            mock_ssh_client.return_value.close.assert_not_called()
            sys.stdout = sys.__stdout__
            self.assertNotIn("SSH connection closed.", captured_output.getvalue())


if __name__ == "__main__":
    unittest.main()
