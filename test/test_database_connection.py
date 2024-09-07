import sys
import os
import unittest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


from unittest.mock import MagicMock, patch

# Für Dockercontainer zum Initialisieren der lokalen Module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../Datenspeicherung/Python')))
# Deine Importe für die zu testenden Funktionen
import database_connection as db_conn

def test_create_session_real_engine():
    engine = create_engine('sqlite:///:memory:')  # Eine SQLite-In-Memory-Datenbank
    session = db_conn.create_session(engine)
    
    assert session is not None, "Session sollte erfolgreich erstellt werden"
    session.close()
    
class TestDatabaseConnection(unittest.TestCase):


    # Tests für die Methode validate_db_config
    @patch('database_connection.validate_db_config')
    def test_validate_db_config_success(self, mock_validate_db_config):
        # Mock the return value
        mock_validate_db_config.return_value = True
        
        # Perform the test
        result = db_conn.validate_db_config('mock_user', 'mock_password', 'mock_host', 'mock_port', 'mock_name')
        self.assertTrue(result)
    
    @patch('database_connection.validate_db_config')
    def test_validate_db_config_failure(self, mock_validate_db_config):
        # Mock the return value to simulate failure
        mock_validate_db_config.return_value = False
        
        # Perform the test
        result = db_conn.validate_db_config('mock_user', 'mock_password', 'mock_host', 'mock_port', 'mock_name')
        self.assertFalse(result)
    
    # Test für create session
    @patch('database_connection.sessionmaker')
    def test_create_session_success(self, mock_sessionmaker):
        # Erstelle einen Mock für die Session
        mock_session = MagicMock()
        
        # Setze den return_value des sessionmaker-Objekts
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        
        # Engine als Mock-Objekt
        engine = MagicMock()
        
        # Rufe die zu testende Funktion auf
        session = db_conn.create_session(engine)
        
        # Überprüfen, ob sessionmaker mit der richtigen Engine aufgerufen wurde
        mock_sessionmaker.assert_called_once_with(bind=engine)
        
        # Überprüfe, ob die Rückgabe korrekt ist
        self.assertEqual(session, mock_session)

    @patch('logging.exception')
    @patch('database_connection.sessionmaker')
    def test_create_session_failure(self, mock_sessionmaker, mock_logging_exception):
        print(mock_logging_exception.call_args)

        # Simuliere, dass sessionmaker eine Exception auslöst
        mock_sessionmaker.side_effect = SQLAlchemyError("Session creation failed")
        
        # Engine als Mock-Objekt
        engine = MagicMock()
        
        # Rufe die zu testende Funktion auf
        session = db_conn.create_session(engine)
        
        # Überprüfen, ob sessionmaker aufgerufen wurde
        mock_sessionmaker.assert_called_once_with(bind=engine)
        
        # Überprüfen, ob None zurückgegeben wurde
        self.assertIsNone(session)
        
        # Überprüfen, ob logging.exception überhaupt aufgerufen wurde
        mock_logging_exception.assert_called_once()

        # Optional: Überprüfen, ob die Nachricht "Session creation failed" im Log enthalten ist
        mock_logging_exception.assert_called_once_with("Session creation failed")


    # Tests für Main Methode
    @patch('database_connection.orm.create_tables')
    @patch('database_connection.create_session')
    @patch('database_connection.connect_to_db')
    @patch('database_connection.logging')
    def test_main_session_commit_failure(self, mock_logging, mock_connect_to_db, mock_create_session, mock_create_tables):
        # Mock session and its commit method to raise an exception
        mock_session = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Commit error")
        
        # Set up mocks
        mock_create_session.return_value = mock_session
        mock_connect_to_db.return_value = MagicMock()
        mock_create_tables.return_value = None  # Wenn create_tables keine Rückgabewerte hat

        # Test logic here
        db_conn.main()

        # Überprüfe, ob session.rollback aufgerufen wurde
        mock_session.rollback.assert_called_once()

        # Überprüfen, ob logging.error aufgerufen wurde
        mock_logging.error.assert_called_once_with("Failed to commit session: Commit error")

        # Überprüfe, ob create_tables einmal aufgerufen wurde
        mock_create_tables.assert_called_once()

    @patch('database_connection.connect_to_db')
    def test_connect_to_db_success(self, mock_connect_to_db):
        # Mock the connection return value
        mock_connect_to_db.return_value = True
        
        # Perform the test
        result = db_conn.connect_to_db('mock_user', 'mock_password', 'mock_host', 'mock_port', 'mock_name')
        self.assertTrue(result)
    
    @patch('database_connection.connect_to_db')
    def test_connect_to_db_failure(self, mock_connect_to_db):
        # Mock the connection to simulate failure
        mock_connect_to_db.side_effect = Exception("Connection failed")
        
        # Test that the connection failure is handled
        with self.assertRaises(Exception):
            db_conn.connect_to_db('mock_user', 'mock_password', 'mock_host', 'mock_port', 'mock_name')


if __name__ == '__main__':
    unittest.main()

