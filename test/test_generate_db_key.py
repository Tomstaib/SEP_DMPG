import sys
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Für Dockercontainer zum Initialisieren der lokalen Module
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Datenspeicherung/Python')
))

from generate_db_key import create_pgpass_file, input_password, main

class TestGenerateDBKey(unittest.TestCase):

    @patch('generate_db_key.getpass', return_value='my_password')
    @patch('sys.stdin.isatty', return_value=True)
    def test_input_password_interactive(self, mock_isatty, mock_getpass):
        password = input_password("Enter password")
        self.assertEqual(password, "my_password")

    @patch('sys.stdin.isatty', return_value=False)
    def test_input_password_non_interactive(self, mock_isatty):
        with self.assertRaises(SystemExit):
            input_password("Enter password")

    @patch('os.makedirs')
    @patch('builtins.open')
    @patch('os.chmod')
    def test_create_pgpass_file_unix(self, mock_chmod, mock_open, mock_makedirs):
        mock_open.return_value = MagicMock()

        create_pgpass_file()

        mock_makedirs.assert_called_once()
        mock_open.assert_called_once()
        mock_chmod.assert_called_once()

    @patch('generate_db_key.getpass', side_effect=Exception("Test exception"))
    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.print')
    def test_input_password_exception(self, mock_print, mock_isatty, mock_getpass):
        # Test when an exception is raised during getpass
        result = input_password("Enter password")
        self.assertIsNone(result)
        
        # Ensure that 'print' is called twice: once for the stdin check and once for the exception
        mock_print.assert_any_call("stdin is interactive, prompting for password")
        mock_print.assert_any_call("Error with getpass: Test exception")
        self.assertEqual(mock_print.call_count, 2)

class TestCreatePgPassFileEdgeCases(unittest.TestCase):

    @patch('os.name', 'nt')
    @patch('os.getenv', return_value=None)
    def test_create_pgpass_file_missing_appdata(self, mock_getenv):
        """Test, wenn die APPDATA-Umgebungsvariable unter Windows fehlt."""
        with self.assertRaises(ValueError) as context:
            create_pgpass_file()
        self.assertIn("APPDATA-Umgebungsvariable ist nicht gesetzt", str(context.exception))

    @patch('os.name', 'posix')
    @patch('os.path.expanduser', return_value='')
    def test_create_pgpass_file_missing_home_directory(self, mock_expanduser):
        """Test, wenn das Home-Verzeichnis unter Unix/Linux/Mac nicht zugänglich ist."""
        with self.assertRaises(ValueError) as context:
            create_pgpass_file()
        self.assertIn("Home-Verzeichnis konnte nicht ermittelt werden", str(context.exception))

    @patch('os.name', 'posix')
    @patch('os.makedirs', side_effect=PermissionError("Keine Berechtigung, Verzeichnis zu erstellen"))
    def test_create_pgpass_file_permission_error(self, mock_makedirs):
        """Test, wenn das Erstellen des Verzeichnisses aufgrund von Berechtigungsproblemen fehlschlägt."""
        with self.assertRaises(PermissionError) as context:
            create_pgpass_file()
        self.assertIn("Keine Berechtigung", str(context.exception))

    @patch('os.name', 'posix')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.chmod', side_effect=OSError("Fehler beim Setzen der Dateiberechtigungen"))
    def test_create_pgpass_file_chmod_failure(self, mock_chmod, mock_open, mock_makedirs):
        """Test, wenn das Setzen der Dateiberechtigungen unter Unix/Linux/Mac fehlschlägt."""
        with self.assertRaises(OSError) as context:
            create_pgpass_file()
        self.assertIn("Fehler beim Setzen der Dateiberechtigungen", str(context.exception))

    @patch('os.name', 'posix')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_pgpass_file_write_failure(self, mock_open, mock_makedirs):
        """Test, wenn das Schreiben in die Datei fehlschlägt."""
        mock_open.side_effect = OSError("Fehler beim Schreiben der Datei")
        with self.assertRaises(OSError) as context:
            create_pgpass_file()
        self.assertIn("Fehler beim Schreiben der .pgpass-Datei", str(context.exception))

    @patch('os.name', 'nt')
    @patch('os.getenv', return_value='C:\\Users\\TestUser\\AppData\\Roaming')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_pgpass_file_windows_success(self, mock_open, mock_makedirs, mock_getenv):
        """Test, wenn die pgpass.conf-Datei erfolgreich unter Windows erstellt wird."""
        create_pgpass_file()
        mock_makedirs.assert_called_once_with(os.path.join('C:\\Users\\TestUser\\AppData\\Roaming', 'postgresql'), exist_ok=True)
        mock_open.assert_called_once_with(os.path.join('C:\\Users\\TestUser\\AppData\\Roaming', 'postgresql', 'pgpass.conf'), 'w')

@patch('generate_db_key.DB_PASSWORD', 'oishooX2iefeiNai')
@patch('generate_db_key.DB_HOST', 'imt-sep-001.lin.hs-osnabrueck.de')
@patch('generate_db_key.DB_PORT', '55432')
@patch('generate_db_key.DB_NAME', 'distributed_computing')
@patch('generate_db_key.DB_USER', 'sep')
class TestMainFunction(unittest.TestCase):

    @patch('generate_db_key.create_pgpass_file')
    @patch('generate_db_key.connect_to_db', return_value=None)
    def test_main_no_connection(self, mock_connect, mock_create_pgpass):
        """Test, wenn die Verbindung zur Datenbank fehlschlägt."""
        main()
        mock_create_pgpass.assert_called_once_with('imt-sep-001.lin.hs-osnabrueck.de:55432:distributed_computing:sep:oishooX2iefeiNai')
        mock_connect.assert_called_once()

    @patch('generate_db_key.create_pgpass_file')
    @patch('generate_db_key.connect_to_db')
    @patch('builtins.print')
    def test_main_successful_connection(self, mock_print, mock_connect, mock_create_pgpass):
        """Test, wenn die Verbindung zur Datenbank erfolgreich ist."""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        main()

        mock_create_pgpass.assert_called_once_with('imt-sep-001.lin.hs-osnabrueck.de:55432:distributed_computing:sep:oishooX2iefeiNai')
        mock_connect.assert_called_once()
        mock_connection.close.assert_called_once()  # Stellt sicher, dass die Verbindung geschlossen wird
        mock_print.assert_any_call("Connection successful")

@patch('generate_db_key.DB_PASSWORD', '')
@patch('generate_db_key.connect_to_db')
@patch('generate_db_key.create_pgpass_file')
class TestMainFunctionNoPassword(unittest.TestCase):

    def test_main_no_password(self, mock_connect_to_db, mock_create_pgpass):
        """Test when no password is set."""
        with self.assertRaises(ValueError) as context:
            main()
        self.assertIn("Error getting the Password", str(context.exception))
        mock_connect_to_db.assert_not_called()
        mock_create_pgpass.assert_not_called()

if __name__ == '__main__':
    unittest.main()