import os
import sys
import stat
import time
import importlib
from sqlalchemy.exc import OperationalError
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Für Dockercontainer zum Initialisieren der lokalen Module
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Datenspeicherung/Python')
))

# (Lokale) Importe für die zu testenden Funktionen
import generate_db_key
from generate_db_key import input_password, create_pgpass_file, connect_to_db, main


### Testklasse für InputPassword
class TestInputPassword(unittest.TestCase):

    @patch('generate_db_key.getpass', return_value='password123')
    @patch('sys.stdin.isatty', return_value=True)
    def test_input_password_interactive(self, mock_isatty, mock_getpass):
        """Testet die Eingabe des Passworts in einer interaktiven Sitzung."""
        password = input_password()
        self.assertEqual(password, 'password123')
        mock_isatty.assert_called_once()
        mock_getpass.assert_called_once()

    @patch('generate_db_key.getpass', return_value='password123')
    @patch('sys.stdin.isatty', return_value=False)
    @patch('builtins.print')
    def test_input_password_non_interactive(self, mock_print, mock_isatty, mock_getpass):
        """Testet den Abbruch der Passwortabfrage, wenn stdin nicht interaktiv ist."""
        with self.assertRaises(SystemExit) as cm:
            input_password()
        self.assertEqual(cm.exception.code, 1)
        mock_isatty.assert_called_once()
        mock_print.assert_called_with(
            "stdin is not interactive, cannot prompt for password"
        )
        mock_getpass.assert_not_called()

    @patch('generate_db_key.getpass', side_effect=Exception("getpass error"))
    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.print')
    def test_input_password_exception(self, mock_print, mock_isatty, mock_getpass):
        """Testet den Abbruch bei einer Exception während der Passwortabfrage."""
        with self.assertRaises(SystemExit) as cm:
            input_password()
        self.assertEqual(cm.exception.code, 1)
        mock_isatty.assert_called_once()
        mock_getpass.assert_called_once()
        mock_print.assert_called_with("Error with getpass: getpass error")


### Testklasse für CreatePgpassFile
class TestCreatePgpassFile(unittest.TestCase):

    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.chmod")
    @patch("builtins.print")
    def test_create_pgpass_file_existing_dir(self, mock_print, mock_chmod, mock_open, mock_makedirs, mock_exists):
        """Testet das Erstellen der .pgpass-Datei, wenn das Verzeichnis existiert."""
        template = "some_template_data"
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        pgpass_path = os.path.join(downloads_dir, 'pgpass.conf')

        # Aufruf der zu testenden Funktion
        create_pgpass_file(template)

        # Sicherstellen, dass die Datei erstellt wurde, unabhängig vom Vorhandensein des Verzeichnisses
        mock_open.assert_called_once_with(pgpass_path, 'w')
        mock_open().write.assert_called_once_with(template)

        # Überprüfen der Berechtigungen (auf Systemen, die keine Windows-Systeme sind)
        if os.name != 'nt':
            mock_chmod.assert_called_once_with(pgpass_path, stat.S_IRUSR | stat.S_IWUSR)

        mock_print.assert_any_call(f"Saving .pgpass file to: {pgpass_path}")

    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.chmod")
    @patch("builtins.print")
    def test_create_pgpass_file_dir_creation(self, mock_print, mock_chmod, mock_open, mock_makedirs, mock_exists):
        """Testet das Erstellen der .pgpass-Datei und des Verzeichnisses, wenn es nicht existiert."""
        template = "some_template_data"
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        pgpass_path = os.path.join(downloads_dir, 'pgpass.conf')

        # Aufruf der zu testenden Funktion
        create_pgpass_file(template)

        # Sicherstellen, dass os.makedirs aufgerufen wurde, weil das Verzeichnis nicht existiert
        mock_makedirs.assert_called_once_with(downloads_dir, exist_ok=True)

        # Sicherstellen, dass die Datei erstellt wurde
        mock_open.assert_called_once_with(pgpass_path, 'w')
        mock_open().write.assert_called_once_with(template)

        # Überprüfen der Berechtigungen (auf Systemen, die keine Windows-Systeme sind)
        if os.name != 'nt':
            mock_chmod.assert_called_once_with(pgpass_path, stat.S_IRUSR | stat.S_IWUSR)

        mock_print.assert_any_call(f"Saving .pgpass file to: {pgpass_path}")

    ### Edge-Case-Tests
    @patch("os.makedirs", side_effect=PermissionError("No permission to create directory"))
    @patch("builtins.print")
    def test_create_pgpass_file_permission_error(self, mock_print, mock_makedirs):
        """Testet die Behandlung von Berechtigungsfehlern beim Erstellen des Verzeichnisses."""
        template = "some_template_data"
        create_pgpass_file(template)
        mock_print.assert_any_call("Error writing .pgpass file: No permission to create directory")

    @patch("os.chmod", side_effect=OSError("No permission to set permissions"))
    @patch("builtins.print")
    def test_create_pgpass_file_chmod_error(self, mock_print, mock_chmod):
        """Testet die Behandlung von Fehlern beim Setzen der Dateiberechtigungen."""
        template = "some_template_data"
        create_pgpass_file(template)
        mock_print.assert_any_call("Error setting permissions: No permission to set permissions")

    @patch("builtins.open", side_effect=OSError("No space left on device"))
    @patch("builtins.print")
    def test_create_pgpass_file_no_space(self, mock_print, mock_open):
        """Testet den Fehlerfall, wenn kein Speicherplatz mehr verfügbar ist."""
        template = "some_template_data"
        create_pgpass_file(template)
        mock_print.assert_any_call("Error writing .pgpass file: No space left on device")

    ### Performance-Test
    def test_create_pgpass_file_performance(self):
        """Testet die Performance der create_pgpass_file-Funktion."""
        start_time = time.time()
        template = "some_template_data"
        for _ in range(1000):  # Test für 1000 Dateien
            create_pgpass_file(template)
        end_time = time.time()
        self.assertLess(end_time - start_time, 10)  # Muss in weniger als 10 Sekunden durchlaufen


### Testklasse für ConnectToDb
class TestConnectToDb(unittest.TestCase):

    @patch("generate_db_key.create_engine")
    def test_connect_to_db_success(self, mock_create_engine):
        """Testet die erfolgreiche Verbindung zur Datenbank."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()

        # Simuliere, dass die Methode create_engine eine Engine zurückgibt
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value = mock_connection

        # Aufruf der zu testenden Funktion
        connection = connect_to_db()

        # Sicherstellen, dass die Verbindung erfolgreich hergestellt wurde
        self.assertIsNotNone(connection)
        mock_create_engine.assert_called_once()
        mock_engine.connect.assert_called_once()
        self.assertEqual(connection, mock_connection)

    ### Edge-Case: Datenbank nicht erreichbar
    @patch("sqlalchemy.create_engine", side_effect=OperationalError("Could not connect", None, None))
    def test_connect_to_db_failed(self, mock_create_engine):
        """Testet die Fehlerbehandlung, wenn die Datenbank nicht erreichbar ist."""
        connection = connect_to_db()
        self.assertIsNone(connection)


### Integrationstest für `main()`
class TestMain(unittest.TestCase):

    @patch("generate_db_key.connect_to_db", return_value=MagicMock())
    @patch("generate_db_key.create_pgpass_file")
    @patch("generate_db_key.input_password", return_value="test_password")
    @patch("builtins.print")
    def test_main_successful(self, mock_print, mock_input_password, mock_create_pgpass, mock_connect_to_db):
        """Testet den erfolgreichen Ablauf der main-Funktion."""
        main()
        mock_input_password.assert_called_once()
        mock_create_pgpass.assert_called_once_with(f'imt-sep-001.lin.hs-osnabrueck.de:55432:distributed_computing:sep:test_password')
        mock_connect_to_db.assert_called_once()
        mock_print.assert_any_call("Connection successful")

    @patch("generate_db_key.connect_to_db", return_value=None)
    @patch("generate_db_key.create_pgpass_file")
    @patch("generate_db_key.input_password", return_value="test_password")
    @patch("builtins.print")
    def test_main_unsuccessful(self, mock_print, mock_input_password, mock_create_pgpass, mock_connect_to_db):
        """Testet den Ablauf, wenn die Verbindung zur Datenbank fehlschlägt."""
        main()
        mock_input_password.assert_called_once()
        mock_create_pgpass.assert_called_once_with(f'imt-sep-001.lin.hs-osnabrueck.de:55432:distributed_computing:sep:test_password')
        mock_connect_to_db.assert_called_once()
        mock_print.assert_any_call("Connection unsuccessful")

    @patch("generate_db_key.input_password", return_value=None)
    def test_main_no_password(self, mock_input_password):
        """Testet, dass ein Fehler geworfen wird, wenn kein Passwort eingegeben wird."""
        with self.assertRaises(ValueError, msg="Error getting the Password"):
            main()


class TestMainExecution(unittest.TestCase):

    @patch('generate_db_key.connect_to_db', return_value=MagicMock())
    @patch('generate_db_key.create_pgpass_file')
    @patch('generate_db_key.input_password', return_value="test_password")
    @patch("builtins.print")
    @patch("sys.exit")  # Patching sys.exit to prevent it from stopping the test
    def test_main_function(self, mock_exit, mock_print, mock_input_password, mock_create_pgpass, mock_connect_to_db):
        """Testet die main-Funktion, ohne den Test durch sys.exit zu beenden."""
        generate_db_key.main()

        # Sicherstellen, dass create_pgpass_file mit den richtigen Parametern aufgerufen wurde
        mock_create_pgpass.assert_called_once_with(f'imt-sep-001.lin.hs-osnabrueck.de:55432:distributed_computing:sep:test_password')

        # Sicherstellen, dass die Verbindung hergestellt und geschlossen wurde
        mock_connect_to_db.assert_called_once()
        mock_connect_to_db.return_value.close.assert_called_once()

        # Sicherstellen, dass die Erfolgsmeldung gedruckt wurde
        mock_print.assert_any_call("Connection successful")


if __name__ == '__main__':
    unittest.main()
