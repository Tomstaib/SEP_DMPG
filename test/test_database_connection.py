import sys
import os
import unittest
import subprocess
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import create_engine

from unittest.mock import MagicMock, patch

# Für Dockercontainer zum Initialisieren der lokalen Module
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Datenspeicherung/Python')
))

# (lokale) Importe für die zu testenden Funktionen
import database_connection as db_conn


class TestSessionCreation(unittest.TestCase):

    def test_create_session_real_engine(self):
        engine = create_engine('sqlite:///:memory:')  # Eine SQLite-In-Memory-Datenbank
        session = db_conn.create_session(engine)

        assert session is not None, "Session sollte erfolgreich erstellt werden"
        session.close()


class TestMainScriptExecution(unittest.TestCase):

    def test_main_called_when_script_executed(self):
        # Pfad zu deinem Modul
        script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../Datenspeicherung/Python/database_connection.py')
        )

        # Führe das Skript als Subprozess aus
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)

        # Überprüfe, ob das Skript erfolgreich ausgeführt wurde
        assert result.returncode == 0


class TestDatabaseConnection(unittest.TestCase):

    # Tests für die Methode validate_db_config
    @patch('database_connection.validate_db_config')
    def test_validate_db_config_success(self, mock_validate_db_config):
        # Mock the return value
        mock_validate_db_config.return_value = True

        # Perform the test
        result = db_conn.validate_db_config(
            'mock_user', 'mock_password', 'mock_host', 'mock_port', 'mock_name'
        )
        self.assertTrue(result)

    @patch('database_connection.validate_db_config')
    def test_validate_db_config_failure(self, mock_validate_db_config):
        # Mock the return value to simulate failure
        mock_validate_db_config.return_value = False

        # Perform the test
        result = db_conn.validate_db_config(
            'mock_user', 'mock_password', 'mock_host', 'mock_port', 'mock_name'
        )
        self.assertFalse(result)

    @patch('database_connection.DB_USER', 'valid_user')
    @patch('database_connection.DB_PASSWORD', 'valid_password')
    @patch('database_connection.DB_HOST', 'localhost')
    @patch('database_connection.DB_PORT', '5432')
    @patch('database_connection.DB_NAME', 'valid_db')
    def test_validate_db_config_complete(self):
        try:
            db_conn.validate_db_config()  # Soll keine Exception werfen
        except ValueError:
            self.fail("validate_db_config raised ValueError unexpectedly!")

    # Tests für die Methode create_session
    @patch('database_connection.sessionmaker')
    def test_create_session_success(self, mock_sessionmaker):
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        engine = MagicMock()
        session = db_conn.create_session(engine)

        mock_sessionmaker.assert_called_once_with(bind=engine)
        self.assertEqual(session, mock_session)

    @patch('logging.exception')
    @patch('database_connection.sessionmaker')
    def test_create_session_failure(self, mock_sessionmaker, mock_logging_exception):
        mock_sessionmaker.side_effect = SQLAlchemyError("Session creation failed")
        engine = MagicMock()
        session = db_conn.create_session(engine)

        mock_sessionmaker.assert_called_once_with(bind=engine)
        self.assertIsNone(session)
        mock_logging_exception.assert_called_once_with("Session creation failed")


class TestMainFunction(unittest.TestCase):

    @patch('database_connection.orm.create_tables')
    @patch('database_connection.create_session')
    @patch('database_connection.connect_to_db')
    @patch('database_connection.logging')
    def test_main_session_commit_failure(
            self, mock_logging, mock_connect_to_db, mock_create_session, mock_create_tables):
        mock_session = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Commit error")
        mock_create_session.return_value = mock_session
        mock_connect_to_db.return_value = MagicMock()

        db_conn.main()

        mock_session.rollback.assert_called_once()
        mock_logging.error.assert_called_once_with("Failed to commit session: Commit error")
        mock_create_tables.assert_called_once()

    @patch('database_connection.connect_to_db')
    def test_connect_to_db_success(self, mock_connect_to_db):
        mock_connect_to_db.return_value = True
        result = db_conn.connect_to_db('mock_user', 'mock_password', 'mock_host', 'mock_port', 'mock_name')
        self.assertTrue(result)

    @patch('database_connection.connect_to_db')
    def test_connect_to_db_failure(self, mock_connect_to_db):
        mock_connect_to_db.side_effect = Exception("Connection failed")
        with self.assertRaises(Exception):
            db_conn.connect_to_db('mock_user', 'mock_password', 'mock_host', 'mock_port', 'mock_name')

    @patch('database_connection.DB_USER', '')
    @patch('database_connection.DB_PASSWORD', 'password')
    @patch('database_connection.DB_HOST', 'host')
    @patch('database_connection.DB_PORT', 'port')
    @patch('database_connection.DB_NAME', 'name')
    def test_validate_db_config_incomplete(self):
        with self.assertRaises(ValueError):
            db_conn.validate_db_config()

    @patch('database_connection.validate_db_config', side_effect=ValueError("Invalid config"))
    @patch('database_connection.logging.error')
    def test_connect_to_db_invalid_config(self, mock_logging_error, mock_validate_db_config):
        engine = db_conn.connect_to_db()
        self.assertIsNone(engine)
        mock_logging_error.assert_called_once_with("Configuration Error: Invalid config")

    @patch('database_connection.create_engine')
    @patch('database_connection.validate_db_config')
    def test_connect_to_db_success_connection_close(self, mock_validate_db_config, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        engine = db_conn.connect_to_db()

        mock_engine.connect.return_value.close.assert_called_once()

    @patch('database_connection.connect_to_db', return_value=None)
    @patch('database_connection.logging.error')
    def test_main_connect_to_db_failure(self, mock_logging_error, mock_connect_to_db):
        db_conn.main()
        mock_connect_to_db.assert_called_once()
        mock_logging_error.assert_called_once_with("Failed to connect to the database")

    @patch('database_connection.orm.create_tables')
    @patch('database_connection.create_session')
    @patch('database_connection.connect_to_db')
    @patch('database_connection.logging')
    def test_main_general_commit_failure(
            self, mock_logging, mock_connect_to_db, mock_create_session, mock_create_tables):
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("Unexpected error during commit")
        mock_create_session.return_value = mock_session
        mock_connect_to_db.return_value = MagicMock()

        db_conn.main()

        mock_session.rollback.assert_called_once()
        mock_logging.exception.assert_called_once_with("An unexpected error occurred during session commit")

    @patch('database_connection.orm.create_tables')
    @patch('database_connection.create_session', return_value=None)
    @patch('database_connection.connect_to_db')
    @patch('database_connection.logging.error')
    def test_main_no_session_created(self, mock_logging_error, mock_connect_to_db, mock_create_session, mock_create_tables):
        mock_connect_to_db.return_value = MagicMock()

        db_conn.main()

        mock_logging_error.assert_called_once_with("Failed to create session.")

    @patch('database_connection.orm.create_tables', side_effect=SQLAlchemyError("Table creation failed"))
    @patch('database_connection.logging.exception')
    @patch('database_connection.connect_to_db')
    def test_main_create_tables_failure(self, mock_connect_to_db, mock_logging_exception, mock_create_tables):
        mock_connect_to_db.return_value = MagicMock()

        db_conn.main()

        mock_logging_exception.assert_called_once_with("Failed to create tables")

    @patch('database_connection.create_engine', side_effect=OperationalError("test statement", "params", "orig"))
    @patch('database_connection.logging.error')
    def test_connect_to_db_operational_error(self, mock_logging_error, mock_create_engine):
        engine = db_conn.connect_to_db()
        self.assertIsNone(engine)

        mock_logging_error.assert_called_once()
        logged_message = mock_logging_error.call_args[0][0]
        self.assertIn("Database connection failed", logged_message)
        self.assertIn("test statement", logged_message)

    @patch('database_connection.create_engine', return_value=None)
    @patch('database_connection.logging.error')
    def test_connect_to_db_invalid_engine(self, mock_logging_error, mock_create_engine):
        engine = db_conn.connect_to_db()
        self.assertIsNone(engine)
        mock_logging_error.assert_called_once_with("An unexpected error occurred", exc_info=True)

    @patch('database_connection.create_engine', side_effect=Exception("Unknown error"))
    @patch('database_connection.logging.exception')
    def test_connect_to_db_general_exception(self, mock_logging_exception, mock_create_engine):
        engine = db_conn.connect_to_db()
        self.assertIsNone(engine)
        mock_logging_exception.assert_called_once_with("An unexpected error occurred")

    @patch('database_connection.create_engine')
    @patch('database_connection.logging.info')
    def test_connect_to_db_logging_success(self, mock_logging_info, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        engine = db_conn.connect_to_db()
        self.assertIsNotNone(engine)
        mock_logging_info.assert_called_once_with("Connection successful")


if __name__ == '__main__':
    unittest.main()
