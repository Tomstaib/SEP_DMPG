import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys
import stat
from sqlalchemy.exc import OperationalError

# Für Dockercontainer zum Initialisieren der lokalen Module
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Datenspeicherung/Python')
))

# (lokale) Importe für die zu testenden Funktionen
from generate_db_key import input_password, create_pgpass_file, connect_to_db


class TestInputPassword(unittest.TestCase):

    @patch('generate_db_key.getpass', return_value='password123')
    @patch('sys.stdin.isatty', return_value=True)
    def test_input_password_interactive(self, mock_isatty, mock_getpass):
        password = input_password()
        self.assertEqual(password, 'password123')
        mock_isatty.assert_called_once()
        mock_getpass.assert_called_once()

    @patch('generate_db_key.getpass', return_value='password123')
    @patch('sys.stdin.isatty', return_value=False)
    @patch('builtins.print')
    def test_input_password_non_interactive(self, mock_print, mock_isatty, mock_getpass):
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
    def test_input_password_exception(self, mock_isatty, mock_getpass):
        with self.assertRaises(SystemExit):
            input_password()


class TestCreatePgpassFile(unittest.TestCase):

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.chmod")
    @patch("builtins.print")
    def test_create_pgpass_file(self, mock_print, mock_chmod, mock_makedirs, mock_open):
        template = "some_template_data"
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        pgpass_path = os.path.join(downloads_dir, 'pgpass.conf')

        create_pgpass_file(template)

        mock_makedirs.assert_called_once_with(
            os.path.dirname(pgpass_path), exist_ok=True
        )
        mock_open.assert_called_once_with(pgpass_path, 'w')
        mock_open().write.assert_called_once_with(template)
        if os.name != 'nt':
            mock_chmod.assert_called_once_with(
                pgpass_path, stat.S_IRUSR | stat.S_IWUSR
            )
        mock_print.assert_any_call(f"Saving .pgpass file to: {pgpass_path}")

    @patch("os.makedirs", side_effect=Exception("makedirs error"))
    @patch("builtins.print")
    def test_create_pgpass_file_makedirs_error(self, mock_print, mock_makedirs):
        template = "some_template_data"
        create_pgpass_file(template)
        mock_print.assert_any_call("Error writing .pgpass file: makedirs error")


class TestConnectToDb(unittest.TestCase):

    @patch("sqlalchemy.create_engine")
    @patch("builtins.print")
    def test_connect_to_db_success(self, mock_print, mock_create_engine):
        # Mock für die SQLAlchemy-Engine und die Verbindung
        mock_engine = MagicMock()
        mock_connection = MagicMock()

        # create_engine gibt mock_engine zurück
        mock_create_engine.return_value = mock_engine

        # Verbindung simulieren
        mock_engine.connect.return_value = mock_connection

        # Rufe die Funktion auf
        connection = connect_to_db()

        # Sicherstellen, dass die Verbindung nicht None ist
        self.assertIsNotNone(connection)
        self.assertEqual(connection, mock_connection)

        # Überprüfe, ob "Connection successful" ausgegeben wurde
        mock_print.assert_any_call("Connection successful")

    @patch("sqlalchemy.create_engine")
    @patch("builtins.print")
    def test_connect_to_db_failed(self, mock_print, mock_create_engine):
        mock_engine = mock_create_engine.return_value
        mock_engine.connect.side_effect = OperationalError(
            "Could not connect", None, None
        )

        connection = connect_to_db()

        self.assertIsNone(connection)
        error_message_found = any(
            "Error" in call[0][0] for call in mock_print.call_args_list
        )
        self.assertTrue(error_message_found)

    @patch("sqlalchemy.create_engine")
    @patch("builtins.print")
    def test_connect_to_db_exception(self, mock_print, mock_create_engine):
        # Simuliere einen allgemeinen Fehler bei der Erstellung der Engine
        mock_create_engine.side_effect = Exception("General error")

        connection = connect_to_db()

        self.assertIsNone(connection)
        error_message_found = any(
            "Error" in call[0][0] for call in mock_print.call_args_list
        )
        self.assertTrue(error_message_found)

    @patch("sqlalchemy.create_engine")
    @patch("builtins.print")
    def test_connect_to_db_error_handling(self, mock_print, mock_create_engine):
        # Simuliere einen Fehler bei der Engine-Erstellung
        mock_create_engine.side_effect = Exception("create_engine error")
        connection = connect_to_db()
        self.assertIsNone(connection)
        mock_print.assert_any_call("Error: create_engine error")


if __name__ == '__main__':
    unittest.main()
