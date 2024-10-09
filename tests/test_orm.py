import sys
import os
import unittest

from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker as sa_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Datenspeicherung', 'Python')))

from orm import Base, HSUser, Model, Scenario, create_tables, main
from database_params import DB_USER, DB_HOST, DB_PORT, DB_NAME


class TestORM(unittest.TestCase):

    def setUp(self):
        # Use an in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        Session = sa_sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_create_user(self):
        user = HSUser(user_name="test_user")
        self.session.add(user)
        self.session.commit()

        result = self.session.query(HSUser).filter_by(user_name="test_user").one()
        self.assertEqual(result.user_name, "test_user")

    def test_create_model(self):
        user = HSUser(user_name="test_user")
        self.session.add(user)
        self.session.flush()  # Commit the user so we can reference the user_id

        model = Model(model_name="test_model", user_id=user.user_id)
        self.session.add(model)
        self.session.commit()

        result = self.session.query(Model).filter_by(model_name="test_model").one()
        self.assertEqual(result.model_name, "test_model")
        self.assertEqual(result.user_id, user.user_id)

    def test_create_scenario(self):
        user = HSUser(user_name="test_user")
        self.session.add(user)
        self.session.flush()

        model = Model(model_name="test_model", user_id=user.user_id)
        self.session.add(model)
        self.session.flush()

        scenario = Scenario(scenario_name="test_scenario", model_id=model.model_id)
        self.session.add(scenario)
        self.session.commit()

        result = self.session.query(Scenario).filter_by(scenario_name="test_scenario").one()
        self.assertEqual(result.scenario_name, "test_scenario")
        self.assertEqual(result.model_id, model.model_id)


class TestCreateTables(unittest.TestCase):
    """
    Test class for the create_tables function. Ensures that tables are correctly created.
    """

    @patch('orm.create_engine')
    @patch('orm.Base.metadata.create_all')
    def test_create_tables(self, mock_create_all, mock_create_engine):
        """Tests whether create_engine and create_all are called correctly."""
        
        # Simulate an engine return value
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        create_tables()

        # Check if create_engine was called with the correct URL
        expected_db_url = f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        mock_create_engine.assert_called_once_with(expected_db_url)

        # Check if create_all was called on the engine
        mock_create_all.assert_called_once_with(mock_engine)


class TestORMMainIntegration(unittest.TestCase):
    """
    Integration test for the main() function.
    Tests the entire chain of operations in main(), from DB connection to table creation and session commit.
    """

    @patch('logging.error')
    @patch('logging.info')
    @patch('logging.exception')
    @patch('orm.create_tables')  
    def test_main_integration_success(self, mock_create_tables, mock_logging_exception, mock_logging_info, mock_logging_error):
        """Integration test for the success case of the main() function."""
        mock_engine = MagicMock()
        mock_session = MagicMock()

        with patch('database_connection.connect_to_db', return_value=mock_engine), \
             patch('database_connection.create_session', return_value=mock_session):
            main()

            mock_create_tables.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_logging_info.assert_any_call("Tables created")
            mock_logging_info.assert_any_call("Session committed successfully")
            mock_logging_error.assert_not_called()

    @patch('logging.error')
    @patch('logging.exception')
    @patch('orm.create_tables', side_effect=SQLAlchemyError("Failed to create tables"))
    def test_main_integration_create_tables_exception(self, mock_create_tables, mock_logging_exception, mock_logging_error):
        """Integration test for the case when create_tables fails."""
        mock_engine = MagicMock()

        with patch('database_connection.connect_to_db', return_value=mock_engine):
            main()

            mock_create_tables.assert_called_once()
            mock_logging_exception.assert_called_once_with("Failed to create tables Failed to create tables")
            mock_logging_error.assert_not_called()

    @patch('logging.error')
    @patch('logging.info')
    @patch('logging.exception')
    @patch('orm.create_tables')
    def test_main_integration_no_session(self, mock_create_tables, mock_logging_exception, mock_logging_info, mock_logging_error):
        """Integration test for the case when session creation fails."""
        mock_engine = MagicMock()

        with patch('database_connection.connect_to_db', return_value=mock_engine), \
             patch('database_connection.create_session', return_value=None):
            main()

            mock_create_tables.assert_called_once()
            mock_logging_error.assert_called_once_with("Failed to create session.")
            mock_logging_exception.assert_not_called()

    @patch('logging.error')
    @patch('logging.exception')
    @patch('orm.create_tables')
    def test_main_integration_no_db_connection(self, mock_create_tables, mock_logging_exception, mock_logging_error):
        """Integration test for the case when no database connection can be established."""
        with patch('database_connection.connect_to_db', return_value=None):
            main()

            mock_create_tables.assert_not_called()
            mock_logging_error.assert_called_once_with("Failed to connect to the database")
            mock_logging_exception.assert_not_called()


class TestSessionCommitException(unittest.TestCase):
    """
    Test class for exception handling during session commit in the main function.
    Ensures rollback is performed and errors are logged in case of SQLAlchemyError or unexpected exceptions.
    """

    @patch('orm.logging.error')
    @patch('orm.database_connection.create_session')
    @patch('orm.database_connection.connect_to_db')
    @patch('orm.create_tables') 
    def test_commit_sqlalchemy_error(self, mock_create_tables, mock_connect_to_db, mock_create_session, mock_logging_error):
        """Tests SQLAlchemyError during commit and ensures rollback and logging are called."""
        
        # Simulate a successful DB connection and session creation
        mock_engine = MagicMock()
        mock_connect_to_db.return_value = mock_engine
        mock_session = MagicMock()
        mock_create_session.return_value = mock_session

        # Simulate SQLAlchemyError during commit
        mock_session.commit.side_effect = SQLAlchemyError("Mocked SQLAlchemyError")

        main()

        mock_session.rollback.assert_called_once()

        mock_logging_error.assert_called_once_with("Failed to commit session: Mocked SQLAlchemyError")

    @patch('orm.logging.exception')
    @patch('orm.database_connection.create_session')
    @patch('orm.database_connection.connect_to_db')
    @patch('orm.create_tables')
    def test_commit_generic_exception(self, mock_create_tables, mock_connect_to_db, mock_create_session, mock_logging_exception):
        """Tests whether rollback and logging are correctly called in case of a general exception."""
        
        mock_engine = MagicMock()
        mock_connect_to_db.return_value = mock_engine
        mock_session = MagicMock()
        mock_create_session.return_value = mock_session

        mock_session.commit.side_effect = Exception("Mocked general exception")

        main()

        mock_session.rollback.assert_called_once()

        mock_logging_exception.assert_called_once_with("An unexpected error occurred during session commit Mocked general exception")


if __name__ == '__main__':
    unittest.main()
