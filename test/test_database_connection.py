import sys
import os
import unittest

from pandas import DataFrame
from unittest.mock import patch, MagicMock, ANY
from sqlalchemy.sql import text
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.exc import IntegrityError, NoResultFound, MultipleResultsFound, SQLAlchemyError, OperationalError


sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Datenspeicherung/Python')
))

from database_connection import (
    validate_db_config,
    connect_to_db,
    get_or_create_user,
    get_or_create_model,
    get_model_id,
    get_scenario_id,
    get_user_id,
    get_or_create_scenario,
    create_session,
    commit_session,
    save_to_db,
    Model,
    Scenario,
    )

class TestDatabaseConfig(unittest.TestCase):
    """
    Test class for the validate_db_config function. Ensures that all necessary configuration fields are checked.
    """

    @patch('database_connection.DB_USER', new=None)  # Simulate missing DB_USER
    @patch('database_connection.DB_HOST', new="localhost")
    @patch('database_connection.DB_PORT', new="5432")
    @patch('database_connection.DB_NAME', new="test_db")
    def test_validate_db_config_missing_user(self):
        """Test that a ValueError is raised if DB_USER is missing."""
        with self.assertRaises(ValueError) as context:
            validate_db_config()
        self.assertIn("Database configuration is incomplete", str(context.exception))

    @patch('database_connection.DB_USER', new="test_user")
    @patch('database_connection.DB_HOST', new=None)  # Simulate missing DB_HOST
    @patch('database_connection.DB_PORT', new="5432")
    @patch('database_connection.DB_NAME', new="test_db")
    def test_validate_db_config_missing_host(self):
        """Test that a ValueError is raised if DB_HOST is missing."""
        with self.assertRaises(ValueError) as context:
            validate_db_config()
        self.assertIn("Database configuration is incomplete", str(context.exception))

    @patch('database_connection.DB_USER', new="test_user")
    @patch('database_connection.DB_HOST', new="localhost")
    @patch('database_connection.DB_PORT', new=None)  # Simulate missing DB_PORT
    @patch('database_connection.DB_NAME', new="test_db")
    def test_validate_db_config_missing_port(self):
        """Test that a ValueError is raised if DB_PORT is missing."""
        with self.assertRaises(ValueError) as context:
            validate_db_config()
        self.assertIn("Database configuration is incomplete", str(context.exception))

    @patch('database_connection.DB_USER', new="test_user")
    @patch('database_connection.DB_HOST', new="localhost")
    @patch('database_connection.DB_PORT', new="5432")
    @patch('database_connection.DB_NAME', new=None)  # Simulate missing DB_NAME
    def test_validate_db_config_missing_name(self):
        """Test that a ValueError is raised if DB_NAME is missing."""
        with self.assertRaises(ValueError) as context:
            validate_db_config()
        self.assertIn("Database configuration is incomplete", str(context.exception))

    @patch('database_connection.DB_USER', new="test_user")
    @patch('database_connection.DB_HOST', new="localhost")
    @patch('database_connection.DB_PORT', new="5432")
    @patch('database_connection.DB_NAME', new="test_db")
    def test_validate_db_config_success(self):
        """Test that no exception is raised when all configurations are provided."""
        try:
            validate_db_config()
        except ValueError:
            self.fail("validate_db_config raised ValueError unexpectedly!")

class TestDatabaseConnection(unittest.TestCase):

    @patch('database_connection.create_engine')
    def test_connect_to_db_success(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        engine = connect_to_db()
        self.assertIsNotNone(engine)
        mock_engine.connect.assert_called_once()

    @patch('database_connection.create_engine')
    def test_connect_to_db_failure(self, mock_create_engine):
        mock_create_engine.side_effect = Exception("Connection Error")
        engine = connect_to_db()
        self.assertIsNone(engine)

    def test_get_or_create_user_existing(self):
        mock_session = MagicMock()
        mock_session.query().filter_by().one_or_none.return_value = MagicMock(user_id=1)

        user_id = get_or_create_user(mock_session, "test_user")
        self.assertEqual(user_id, 1)

    def test_get_or_create_user_new(self):
        mock_session = MagicMock()
        # Simuliere, dass kein Benutzer existiert
        mock_session.query().filter_by().one_or_none.return_value = None

        # Stelle sicher, dass der Benutzer erstellt und eine ID zugewiesen wird
        mock_new_user = MagicMock(user_id=1)
        mock_session.add.side_effect = lambda user: setattr(user, 'user_id', 1)
        mock_session.flush.return_value = None

        user_id = get_or_create_user(mock_session, "new_user")
        self.assertEqual(user_id, 1)

    def test_get_or_create_user_integrity_error(self):
        mock_session = MagicMock()
        mock_session.query().filter_by().one_or_none.side_effect = IntegrityError(None, None, None)

        with self.assertRaises(SQLAlchemyError):
            get_or_create_user(mock_session, "test_user")

    def test_commit_session_success(self):
        mock_session = MagicMock()

        commit_session(mock_session)
        mock_session.commit.assert_called_once()

    def test_commit_session_failure(self):
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("Commit Error")

        commit_session(mock_session)
        mock_session.rollback.assert_called_once()

class TestDatabaseConnectionEdgeCases(unittest.TestCase):
    """
    Test class for edge cases in the database_connection module.
    Ensures that exception handling behaves correctly under unexpected conditions.
    """

    def test_get_or_create_user_integrity_error_user_not_found(self):
        """
        Ensures that SQLAlchemyError is raised when IntegrityError occurs during user creation
        and the user is still not found after rollback.
        """
        mock_session = MagicMock()
        # Simulate no user found initially and after rollback
        mock_session.query().filter_by().one_or_none.side_effect = [None, None]
        # Simulate IntegrityError when flushing
        mock_session.flush.side_effect = IntegrityError(None, None, None)

        with self.assertRaises(SQLAlchemyError) as context:
            get_or_create_user(mock_session, "test_user")

        self.assertIn("User test_user could not be found.", str(context.exception))

    def test_get_or_create_user_integrity_error_user_found_after_rollback(self):
        """
        Edge-case test:
        Ensures that the user_id is returned when IntegrityError occurs during user creation
        and the user is found after rollback.
        """
        mock_session = MagicMock()
        # Simulate no user found initially and user found after rollback
        mock_session.query().filter_by().one_or_none.side_effect = [None, MagicMock(user_id=1)]
        # Simulate IntegrityError when flushing
        mock_session.flush.side_effect = IntegrityError(None, None, None)

        user_id = get_or_create_user(mock_session, "test_user")
        self.assertEqual(user_id, 1)
        mock_session.rollback.assert_called_once()

        # Ensure that add and flush were called once during user creation attempt
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

class TestModelOperationsEdgeCase(unittest.TestCase):
    def test_get_or_create_model_existing(self):
        """
        Test: Wenn das Modell existiert, sollte es zurückgegeben werden, ohne ein neues Modell zu erstellen.
        """
        mock_session = MagicMock()
        # Simuliere, dass das Modell existiert
        existing_model = MagicMock()
        mock_session.query().filter_by().with_for_update().one_or_none.return_value = existing_model

        model = get_or_create_model(mock_session, "existing_model", user_id=1)

        # Überprüfen, dass das existierende Modell zurückgegeben wird
        self.assertEqual(model, existing_model)

        # Überprüfen, dass kein neues Modell erstellt wurde
        mock_session.add.assert_not_called()
        mock_session.flush.assert_not_called()

    def test_get_or_create_model_new(self):
        """
        Test: Wenn das Modell nicht existiert, sollte ein neues Modell erstellt werden.
        """
        mock_session = MagicMock()
        # Simuliere, dass kein Modell existiert
        mock_session.query().filter_by().with_for_update().one_or_none.return_value = None

        # Simuliere die Erstellung eines neuen Modells
        new_model = MagicMock(model_id=1)
        def add_side_effect(model):
            model.model_id = 1  # Weise eine model_id zu, nachdem das Modell hinzugefügt wurde
        mock_session.add.side_effect = add_side_effect

        model = get_or_create_model(mock_session, "new_model", user_id=1)

        # Überprüfen, dass das neue Modell zurückgegeben wird
        self.assertEqual(model.model_id, 1)

        # Überprüfen, dass das Modell hinzugefügt und geflusht wurde
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_get_or_create_model_integrity_error_model_not_found_after_rollback(self):
        """
        Test: If IntegrityError occurs and the model is not found after rollback, a SQLAlchemyError should be raised.
        """
        mock_session = MagicMock()

        # Create mocks for the query chains
        # First query chain (with with_for_update())
        first_query = MagicMock()
        first_query.filter_by.return_value = first_query
        first_query.with_for_update.return_value = first_query
        first_query.one_or_none.return_value = None  # Model not found before creation

        # Second query chain (after rollback, without with_for_update())
        second_query = MagicMock()
        second_query.filter_by.return_value = second_query
        second_query.one_or_none.return_value = None  # Model not found after rollback

        # Set the session.query(Model) to return our first_query, then second_query
        def query_side_effect(*args, **kwargs):
            if args[0] == Model:
                if not hasattr(self, 'query_called'):
                    self.query_called = 1
                    return first_query
                else:
                    self.query_called += 1
                    return second_query
            else:
                return MagicMock()

        mock_session.query.side_effect = query_side_effect

        # Simulate an IntegrityError during flush
        mock_session.flush.side_effect = IntegrityError(None, None, None)

        # Now, test that SQLAlchemyError is raised
        with self.assertRaises(SQLAlchemyError) as context:
            get_or_create_model(mock_session, "test_model", user_id=1)

        self.assertIn("Model test_model could not be found.", str(context.exception))

        # Verify that rollback was called
        mock_session.rollback.assert_called_once()

        # Verify that add and flush were called
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()


    def test_get_or_create_model_integrity_error_model_found_after_rollback(self):
        """
        Test: If IntegrityError occurs and the model is found after rollback, it should be returned.
        """
        mock_session = MagicMock()

        # Mock the model to be returned after rollback
        mock_existing_model = MagicMock()
        mock_existing_model.model_id = 1  # Ensure the model has model_id=1

        # First query chain (with with_for_update())
        first_query = MagicMock()
        first_query.filter_by.return_value = first_query
        first_query.with_for_update.return_value = first_query
        first_query.one_or_none.return_value = None  # Model not found before creation

        # Second query chain (after rollback, without with_for_update())
        second_query = MagicMock()
        second_query.filter_by.return_value = second_query
        second_query.one_or_none.return_value = mock_existing_model  # Model found after rollback

        # Set the session.query(Model) to return our first_query, then second_query
        def query_side_effect(*args, **kwargs):
            if args[0] == Model:
                if not hasattr(self, 'query_called'):
                    self.query_called = 1
                    return first_query
                else:
                    self.query_called += 1
                    return second_query
            else:
                return MagicMock()

        mock_session.query.side_effect = query_side_effect

        # Simulate an IntegrityError during flush
        mock_session.flush.side_effect = IntegrityError(None, None, None)

        # Call the function
        model = get_or_create_model(mock_session, "test_model", user_id=1)

        # Verify that the model found after rollback is returned
        self.assertEqual(model.model_id, 1)

        # Verify that rollback was called
        mock_session.rollback.assert_called_once()




    

    
    def test_get_or_create_model_unexpected_exception(self):
        """
        Test: Stellt sicher, dass eine unerwartete Ausnahme korrekt weitergeleitet wird.
        """
        mock_session = MagicMock()
        # Simuliere eine unerwartete Ausnahme
        mock_session.query().filter_by().with_for_update().one_or_none.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception) as context:
            get_or_create_model(mock_session, "test_model", user_id=1)

        self.assertIn("Unexpected error", str(context.exception))
        mock_session.rollback.assert_not_called()  # Rollback sollte nicht aufgerufen werden, wenn keine Datenbankoperation durchgeführt wurde

class TestScenarioOperationsEdgeCase(unittest.TestCase):
    @patch('database_connection.logging.info')
    def test_get_or_create_scenario_existing(self, mock_logging_info):
        """Test: When the scenario already exists, it should be returned."""
        mock_session = MagicMock()
        existing_scenario = MagicMock(scenario_id=1)
        
        # Mock the query chain
        query_mock = MagicMock()
        query_mock.filter_by.return_value = query_mock
        query_mock.with_for_update.return_value = query_mock
        query_mock.one_or_none.return_value = existing_scenario
        mock_session.query.return_value = query_mock

        scenario = get_or_create_scenario(mock_session, "existing_scenario", minutes=60, model_id=1)

        self.assertEqual(scenario, existing_scenario)
        mock_session.add.assert_not_called()
        mock_session.flush.assert_not_called()  # Expect flush NOT to be called
        mock_logging_info.assert_called_once_with("Scenario 'existing_scenario' already exists for model 1.")

    @patch('database_connection.logging.info')
    def test_get_or_create_scenario_new(self, mock_logging_info):
        """Test: When the scenario does not exist, it should be created and returned."""
        mock_session = MagicMock()
        
        # Mock the query chain to return None, simulating that the scenario does not exist
        query_mock = MagicMock()
        query_mock.filter_by.return_value = query_mock
        query_mock.with_for_update.return_value = query_mock
        query_mock.one_or_none.return_value = None
        mock_session.query.return_value = query_mock

        # Simulate assigning scenario_id during session.flush()
        def flush_side_effect():
            scenario = mock_session.add.call_args[0][0]
            scenario.scenario_id = 1  # Assign scenario_id when flushed

        mock_session.flush.side_effect = flush_side_effect

        scenario = get_or_create_scenario(mock_session, "new_scenario", minutes=120, model_id=2)

        self.assertEqual(scenario.scenario_id, 1)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_logging_info.assert_called_once_with("Scenario 'new_scenario' created for model 2.")

    @patch('database_connection.logging.info')
    @patch('database_connection.logging.warning')
    def test_get_or_create_scenario_integrity_error_scenario_found_after_rollback(self, mock_logging_warning, mock_logging_info):
        """Test: If an IntegrityError occurs and the scenario is found after rollback, it should be returned."""
        mock_session = MagicMock()
        
        # Mock the scenario to be returned after rollback
        mock_existing_scenario = MagicMock()
        mock_existing_scenario.scenario_id = 1

        # First query chain (with with_for_update())
        first_query = MagicMock()
        first_query.filter_by.return_value = first_query
        first_query.with_for_update.return_value = first_query
        first_query.one_or_none.return_value = None  # Scenario not found before creation

        # Second query chain (after rollback, without with_for_update())
        second_query = MagicMock()
        second_query.filter_by.return_value = second_query
        second_query.one_or_none.return_value = mock_existing_scenario  # Scenario found after rollback

        # Set up side effect for session.query(Scenario)
        def query_side_effect(*args, **kwargs):
            if args[0] == Scenario:
                if not hasattr(query_side_effect, 'call_count'):
                    query_side_effect.call_count = 1
                    return first_query
                elif query_side_effect.call_count == 1:
                    query_side_effect.call_count += 1
                    return second_query
                else:
                    return MagicMock()
            else:
                return MagicMock()

        mock_session.query.side_effect = query_side_effect

        # Simulate an IntegrityError during session.flush()
        mock_session.flush.side_effect = IntegrityError(None, None, None)

        # Call the function
        scenario = get_or_create_scenario(mock_session, "test_scenario", minutes=60, model_id=1)

        # Verify that the scenario found after rollback is returned
        self.assertEqual(scenario.scenario_id, 1)
        mock_session.rollback.assert_called_once()
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_logging_warning.assert_called_once_with(
            "IntegrityError when trying to create scenario 'test_scenario' for model 1, retrying..."
        )

    @patch('database_connection.logging.warning')
    def test_get_or_create_scenario_integrity_error_scenario_not_found_after_rollback(self, mock_logging_warning):
        """Test: If an IntegrityError occurs and the scenario is not found after rollback, a SQLAlchemyError should be raised."""
        mock_session = MagicMock()
        
        # Both queries return None, simulating scenario not found before and after rollback
        first_query = MagicMock()
        first_query.filter_by.return_value = first_query
        first_query.with_for_update.return_value = first_query
        first_query.one_or_none.return_value = None

        second_query = MagicMock()
        second_query.filter_by.return_value = second_query
        second_query.one_or_none.return_value = None

        # Set up side effect for session.query(Scenario)
        def query_side_effect(*args, **kwargs):
            if args[0] == Scenario:
                if not hasattr(query_side_effect, 'call_count'):
                    query_side_effect.call_count = 1
                    return first_query
                elif query_side_effect.call_count == 1:
                    query_side_effect.call_count += 1
                    return second_query
                else:
                    return MagicMock()
            else:
                return MagicMock()

        mock_session.query.side_effect = query_side_effect

        # Simulate an IntegrityError during session.flush()
        mock_session.flush.side_effect = IntegrityError(None, None, None)

        # Call the function and expect SQLAlchemyError
        with self.assertRaises(SQLAlchemyError) as context:
            get_or_create_scenario(mock_session, "test_scenario", minutes=60, model_id=1)

        self.assertIn("Scenario test_scenario could not be found.", str(context.exception))
        mock_session.rollback.assert_called_once()
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_logging_warning.assert_called_once_with(
            "IntegrityError when trying to create scenario 'test_scenario' for model 1, retrying..."
        )

    def test_get_scenario_id_found(self):
        """Test that get_scenario_id returns the correct scenario_id when the scenario exists."""
        # Mock the session and query result
        mock_session = MagicMock()
        mock_scenario = MagicMock(scenario_id=1)
        mock_session.query().filter_by().one.return_value = mock_scenario

        # Call the function
        scenario_id = get_scenario_id(mock_session, "test_scenario", model_id=1)

        # Assert that the correct scenario_id is returned
        self.assertEqual(scenario_id, 1)
        mock_session.query().filter_by().one.assert_called_once_with()

    def test_get_scenario_id_not_found(self):
        """Test that get_scenario_id returns None when the scenario does not exist (NoResultFound)."""
        # Mock the session to raise NoResultFound
        mock_session = MagicMock()
        mock_session.query().filter_by().one.side_effect = NoResultFound

        # Call the function
        scenario_id = get_scenario_id(mock_session, "nonexistent_scenario", model_id=1)

        # Assert that None is returned when the scenario is not found
        self.assertIsNone(scenario_id)
        mock_session.query().filter_by().one.assert_called_once_with()

    def test_get_scenario_id_multiple_results(self):
        """Test that get_scenario_id raises an error when multiple scenarios are found (MultipleResultsFound)."""
        # Mock the session to raise MultipleResultsFound
        mock_session = MagicMock()
        mock_session.query().filter_by().one.side_effect = MultipleResultsFound

        # Call the function and assert that MultipleResultsFound is raised
        with self.assertRaises(MultipleResultsFound):
            get_scenario_id(mock_session, "duplicate_scenario", model_id=1)

        mock_session.query().filter_by().one.assert_called_once_with()

    def test_get_scenario_id_unexpected_error(self):
        """Test that get_scenario_id propagates an unexpected exception."""
        # Mock the session to raise an unexpected error
        mock_session = MagicMock()
        mock_session.query().filter_by().one.side_effect = Exception("Unexpected error")

        # Call the function and assert that the unexpected error is raised
        with self.assertRaises(Exception) as context:
            get_scenario_id(mock_session, "error_scenario", model_id=1)

        self.assertIn("Unexpected error", str(context.exception))
        mock_session.query().filter_by().one.assert_called_once_with()

class TestConnectToDbEdgeCases(unittest.TestCase):
    """
    Test class for the connect_to_db function's exception handling.
    """

    @patch('database_connection.validate_db_config')
    @patch('database_connection.logging.error')
    def test_connect_to_db_value_error(self, mock_logging_error, mock_validate_db_config):
        """Test that connect_to_db logs a ValueError and returns None when configuration is incomplete."""
        # Simulate validate_db_config raising a ValueError
        mock_validate_db_config.side_effect = ValueError("Missing configuration")

        engine = connect_to_db()

        # Ensure that the engine is None and the correct log message is generated
        self.assertIsNone(engine)
        mock_logging_error.assert_called_once_with("Configuration Error: Missing configuration")

    @patch('database_connection.create_engine')
    @patch('database_connection.logging.error')
    def test_connect_to_db_operational_error(self, mock_logging_error, mock_create_engine):
        """Test that connect_to_db logs an OperationalError and returns None when database connection fails."""
        # Simulate create_engine raising an OperationalError
        mock_create_engine.side_effect = OperationalError("Could not connect", None, None)

        engine = connect_to_db()

        # Ensure that the engine is None and the correct log message is generated
        self.assertIsNone(engine)
        # Check that the error message contains the expected string
        mock_logging_error.assert_called_once()
        self.assertIn("Database connection failed", mock_logging_error.call_args[0][0])

    @patch('database_connection.create_engine')
    @patch('database_connection.logging.exception')
    def test_connect_to_db_unexpected_exception(self, mock_logging_exception, mock_create_engine):
        """Test that connect_to_db logs an unexpected exception and returns None when an unexpected error occurs."""
        # Simulate create_engine raising a general Exception
        mock_create_engine.side_effect = Exception("Unexpected error")

        engine = connect_to_db()

        # Ensure that the engine is None and the correct log message is generated
        self.assertIsNone(engine)
        mock_logging_exception.assert_called_once_with("An unexpected error occurred Unexpected error")

class TestCreateSessionEdgeCases(unittest.TestCase):
    """
    Test class for the create_session function's edge cases.
    """
    @patch('database_connection.Session')
    @patch('database_connection.sessionmaker')
    def test_create_session_success(self, mock_sessionmaker, mock_Session):
        """Test that create_session successfully creates and returns a session."""
        # Simuliere eine erfolgreiche Erstellung der Session
        mock_session = MagicMock()
        mock_Session.return_value = mock_session
        mock_sessionmaker.return_value = MagicMock()

        engine = MagicMock()

        # Rufe die create_session Funktion auf
        session = create_session(engine)

        # Überprüfen, ob sessionmaker korrekt aufgerufen wurde
        mock_sessionmaker.assert_called_once_with(bind=engine)
        # Überprüfen, ob Session korrekt instanziiert wurde
        mock_Session.assert_called_once()

        # Sicherstellen, dass die Session korrekt zurückgegeben wird
        self.assertEqual(session, mock_session)

    @patch('database_connection.logging.exception')
    @patch('database_connection.sessionmaker')
    def test_create_session_exception(self, mock_sessionmaker, mock_logging_exception):
        """Test that create_session returns None and logs an exception when session creation fails."""
        # Simulate an exception being raised when sessionmaker is called
        mock_sessionmaker.side_effect = SQLAlchemyError("Session creation error")

        engine = MagicMock()  # Mock engine

        session = create_session(engine)

        # Check that session is None when an exception is raised
        self.assertIsNone(session)

        # Ensure the correct logging exception was triggered
        mock_logging_exception.assert_called_once()
        self.assertIn("Session creation failed", mock_logging_exception.call_args[0][0])

class TestGetModelId(unittest.TestCase):
    """
    Test class for the get_model_id function.
    Ensures that model IDs are correctly retrieved or None is returned when not found.
    """

    def test_get_model_id_existing(self):
        """Test that get_model_id returns the correct model_id when the model exists."""
        # Arrange
        mock_session = MagicMock()
        mock_model = MagicMock(model_id=1)
        mock_session.query().filter_by().one.return_value = mock_model

        # Act
        result = get_model_id(mock_session, "existing_model", user_id=1)

        # Assert
        self.assertEqual(result, 1)
        mock_session.query().filter_by().one.assert_called_once_with()

    def test_get_model_id_not_found(self):
        """Test that get_model_id returns None when the model does not exist."""
        # Arrange
        mock_session = MagicMock()
        mock_session.query().filter_by().one.side_effect = NoResultFound

        # Act
        result = get_model_id(mock_session, "nonexistent_model", user_id=1)

        # Assert
        self.assertIsNone(result)
        mock_session.query().filter_by().one.assert_called_once_with()

    def test_get_model_id_multiple_results(self):
        """Test that get_model_id raises an exception when multiple models are found."""
        from sqlalchemy.orm.exc import MultipleResultsFound

        # Arrange
        mock_session = MagicMock()
        mock_session.query().filter_by().one.side_effect = MultipleResultsFound

        # Act & Assert
        with self.assertRaises(MultipleResultsFound):
            get_model_id(mock_session, "duplicate_model", user_id=1)
        mock_session.query().filter_by().one.assert_called_once_with()

    def test_get_model_id_unexpected_exception(self):
        """Test that get_model_id propagates unexpected exceptions."""
        # Arrange
        mock_session = MagicMock()
        mock_session.query().filter_by().one.side_effect = Exception("Unexpected error")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            get_model_id(mock_session, "error_model", user_id=1)
        self.assertIn("Unexpected error", str(context.exception))
        mock_session.query().filter_by().one.assert_called_once_with()

class TestGetUserIdEdgeCases(unittest.TestCase):
    """
    Test class for edge cases in the get_user_id function.
    """

    def test_get_user_id_found(self):
        """Test that get_user_id returns the correct user_id when the user exists."""
        # Mock the session and query result
        mock_session = MagicMock()
        mock_user = MagicMock(user_id=1)
        mock_session.query().filter_by().one.return_value = mock_user

        # Call the function
        user_id = get_user_id(mock_session, "existing_user")

        # Assert that the correct user_id is returned
        self.assertEqual(user_id, 1)
        mock_session.query().filter_by().one.assert_called_once_with()

    def test_get_user_id_not_found(self):
        """Test that get_user_id returns None when the user does not exist (NoResultFound)."""
        # Mock the session to raise NoResultFound
        mock_session = MagicMock()
        mock_session.query().filter_by().one.side_effect = NoResultFound

        # Call the function
        user_id = get_user_id(mock_session, "nonexistent_user")

        # Assert that None is returned when the user is not found
        self.assertIsNone(user_id)
        mock_session.query().filter_by().one.assert_called_once_with()

    def test_get_user_id_multiple_results(self):
        """Test that get_user_id raises an error when multiple users are found (MultipleResultsFound)."""
        # Mock the session to raise MultipleResultsFound
        mock_session = MagicMock()
        mock_session.query().filter_by().one.side_effect = MultipleResultsFound

        # Call the function and assert that MultipleResultsFound is raised
        with self.assertRaises(MultipleResultsFound):
            get_user_id(mock_session, "duplicate_user")

        mock_session.query().filter_by().one.assert_called_once_with()

    def test_get_user_id_unexpected_error(self):
        """Test that get_user_id propagates an unexpected exception."""
        # Mock the session to raise an unexpected error
        mock_session = MagicMock()
        mock_session.query().filter_by().one.side_effect = Exception("Unexpected error")

        # Call the function and assert that the unexpected error is raised
        with self.assertRaises(Exception) as context:
            get_user_id(mock_session, "error_user")

        self.assertIn("Unexpected error", str(context.exception))
        mock_session.query().filter_by().one.assert_called_once_with()

class TestSaveToDbEdgeCases(unittest.TestCase):
    """
    Test class for edge cases in the save_to_db function.
    """

    @patch('database_connection.create_session')
    @patch('database_connection.connect_to_db')
    @patch('database_connection.os.getenv')
    def test_save_to_db_missing_config_path(self, mock_getenv, mock_connect_to_db, mock_create_session):
        """Test that save_to_db raises an exception if the CONFIG_PATH environment variable is missing."""
        mock_getenv.return_value = None

        with self.assertRaises(AttributeError):
            save_to_db(DataFrame(), "2024-01-01", "2024-01-02", 60, 5)

        mock_getenv.assert_called_once_with('CONFIG_PATH')

    @patch('database_connection.create_session')
    @patch('database_connection.connect_to_db')
    @patch('database_connection.get_or_create_user')
    @patch('database_connection.get_or_create_model')
    @patch('database_connection.get_or_create_scenario')
    @patch('database_connection.commit_session')
    @patch('database_connection.os.getenv')
    def test_save_to_db_success(self, mock_getenv, mock_commit_session, mock_get_or_create_scenario,
                                mock_get_or_create_model, mock_get_or_create_user, mock_connect_to_db, mock_create_session):
        """Test that save_to_db executes successfully under normal conditions."""
        # Mock necessary calls and return values
        mock_getenv.return_value = "/some/path/to/config"
        mock_connect_to_db.return_value = MagicMock()
        mock_create_session.return_value = MagicMock()
        mock_get_or_create_user.return_value = 1
        mock_get_or_create_model.return_value = MagicMock()
        mock_get_or_create_scenario.return_value = 1

        combined_pivot = DataFrame([{
            'Average': 5.0,
            'Minimum': 3.0,
            'Maximum': 8.0,
            'Half-Width': 2.5
        }], index=[('type1', 'name1', 'stat1')])

        save_to_db(combined_pivot, "2024-01-01", "2024-01-02", 60, 5)

        # Verify that the methods were called correctly
        mock_commit_session.assert_called_once()
        mock_get_or_create_user.assert_called_once()
        mock_get_or_create_model.assert_called_once()
        mock_get_or_create_scenario.assert_called_once()
        mock_create_session.assert_called_once()

    @patch('database_connection.create_session')
    @patch('database_connection.connect_to_db')
    @patch('database_connection.os.getenv')
    def test_save_to_db_session_creation_failure(self, mock_getenv, mock_connect_to_db, mock_create_session):
        """Test that save_to_db raises an exception if session creation fails."""
        mock_getenv.return_value = "/some/path/to/config"
        mock_connect_to_db.return_value = MagicMock()
        mock_create_session.return_value = None  # Simulate session creation failure

        with self.assertRaises(AttributeError):
            save_to_db(DataFrame(), "2024-01-01", "2024-01-02", 60, 5)

        mock_create_session.assert_called_once()

    @patch('database_connection.create_session')
    @patch('database_connection.connect_to_db')
    @patch('database_connection.get_or_create_user')
    @patch('database_connection.get_or_create_model')
    @patch('database_connection.os.getenv')
    def test_save_to_db_get_or_create_user_failure(self, mock_getenv, mock_get_or_create_model, mock_get_or_create_user,
                                                   mock_connect_to_db, mock_create_session):
        """Test that save_to_db raises an exception if get_or_create_user fails."""
        mock_getenv.return_value = "/some/path/to/config"
        mock_connect_to_db.return_value = MagicMock()
        mock_create_session.return_value = MagicMock()

        # Simulate a failure in get_or_create_user
        mock_get_or_create_user.side_effect = SQLAlchemyError("User creation error")

        with self.assertRaises(SQLAlchemyError):
            save_to_db(DataFrame(), "2024-01-01", "2024-01-02", 60, 5)

        mock_get_or_create_user.assert_called_once()

    @patch('database_connection.create_session')
    @patch('database_connection.connect_to_db')
    @patch('database_connection.get_or_create_user')
    @patch('database_connection.get_or_create_model')
    @patch('database_connection.get_or_create_scenario')
    @patch('database_connection.os.getenv')
    def test_save_to_db_lock_failure(self, mock_getenv, mock_get_or_create_scenario, mock_get_or_create_model,
                                     mock_get_or_create_user, mock_connect_to_db, mock_create_session):
        """Test that save_to_db handles failure to acquire advisory lock."""
        mock_getenv.return_value = "/some/path/to/config"
        mock_connect_to_db.return_value = MagicMock()
        mock_session = MagicMock()
        mock_create_session.return_value = mock_session

        # Simulate an error when attempting to acquire the advisory lock
        mock_session.execute.side_effect = SQLAlchemyError("Lock acquisition failure")

        with self.assertRaises(SQLAlchemyError):
            save_to_db(DataFrame(), "2024-01-01", "2024-01-02", 60, 5)

        # Verify that an attempt was made to acquire the lock
        mock_session.execute.assert_any_call(ANY, {"lock_id": 12345})

        # Now check that the SQL executed matches our expected SQL
        found = False
        expected_sql = "SELECT pg_advisory_lock(:lock_id)"
        for call in mock_session.execute.call_args_list:
            args, kwargs = call
            if len(args) >= 1:
                sql_clause = args[0]
                if isinstance(sql_clause, TextClause):  # Use TextClause for the check
                    sql_string = str(sql_clause).strip()
                    if sql_string == expected_sql:
                        found = True
                        break

        self.assertTrue(found, f"Expected SQL '{expected_sql}' was not executed")
        # Verify that the session was rolled back
        mock_session.rollback.assert_called_once()

    @patch('database_connection.create_session')
    @patch('database_connection.connect_to_db')
    @patch('database_connection.get_or_create_user')
    @patch('database_connection.get_or_create_model')
    @patch('database_connection.get_or_create_scenario')
    @patch('database_connection.commit_session')
    @patch('database_connection.os.getenv')
    def test_save_to_db_commit_failure(self, mock_getenv, mock_commit_session, mock_get_or_create_scenario,
                                       mock_get_or_create_model, mock_get_or_create_user, mock_connect_to_db, mock_create_session):
        """Test that save_to_db handles commit failure."""
        mock_getenv.return_value = "/some/path/to/config"
        mock_connect_to_db.return_value = MagicMock()
        mock_create_session.return_value = MagicMock()

        # Simulate failure during commit
        mock_commit_session.side_effect = SQLAlchemyError("Commit failed")

        with self.assertRaises(SQLAlchemyError):
            save_to_db(DataFrame(), "2024-01-01", "2024-01-02", 60, 5)

        mock_commit_session.assert_called_once()

    @patch('database_connection.create_session')
    @patch('database_connection.connect_to_db')
    @patch('database_connection.os.getenv')
    def test_save_to_db_unexpected_exception(self, mock_getenv, mock_connect_to_db, mock_create_session):
        """Test that save_to_db raises and logs unexpected exceptions."""
        mock_getenv.return_value = "/some/path/to/config"
        mock_connect_to_db.return_value = MagicMock()
        mock_create_session.return_value = MagicMock()

        # Simulate unexpected exception during processing
        mock_create_session.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception):
            save_to_db(DataFrame(), "2024-01-01", "2024-01-02", 60, 5)


if __name__ == '__main__':
    unittest.main()
