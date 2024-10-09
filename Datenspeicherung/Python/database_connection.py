import logging
import sys
import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session as sa_sessionmaker, Session as sa_Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError, NoResultFound, IntegrityError

from database_params import DB_USER, DB_HOST, DB_PORT, DB_NAME

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from orm import PivotTable, Simulation, Scenario, Model, HSUser

def validate_db_config():
    """
    Validate that all necessary database configuration variables are set. If not raise a ValueError.
    """
    if not all([DB_USER, DB_HOST, DB_PORT, DB_NAME]):
        raise ValueError("Database configuration is incomplete. Please check all required fields.")


def get_or_create_user(session: sa_Session, user_name: str) -> int:
    """
    Returns the user_id of a user if found, or creates a new user if not found.

    :param session: SQLAlchemy session in which the database is manipulated.
    :param user_name: Username of the current user for the database scheme.

    :return: The user_id of the current user.
    """

    with session.no_autoflush:
        user: HSUser | None = session.query(HSUser).filter_by(user_name=user_name).one_or_none()
        if user:
            return user.user_id
        else:
            try:
                new_user: HSUser = HSUser(user_name=user_name)
                session.add(new_user)
                session.flush()
                return new_user.user_id
            except IntegrityError:
                session.rollback()

                user: HSUser | None = session.query(HSUser).filter_by(user_name=user_name).one_or_none()
                if user:
                    return user.user_id
                else:
                    raise SQLAlchemyError(f"User {user_name} could not be found.")


def get_or_create_model(session: sa_Session, model_name: str, user_id: int) -> Model:
    """
    Returns the model_id of a model if found, or creates a new model if not found.

    :param session: SQLAlchemy session in which the database is manipulated.
    :param model_name: Name of the model to be created or used.
    :param user_id: User ID of the current user needed for referencing the correct model.

    :return: The Model created or found.
    """

    while True:
        try:
            model: Model | None = session.query(Model).filter_by(model_name=model_name,
                                                                 user_id=user_id).with_for_update().one_or_none()

            if model:
                return model
            else:
                new_model: Model = Model(model_name=model_name, user_id=user_id)
                session.add(new_model)
            session.flush()
            return new_model

        except IntegrityError:
            session.rollback()

            model = session.query(Model).filter_by(model_name=model_name, user_id=user_id).one_or_none()
            if model:
                return model
            else:
                raise SQLAlchemyError(f"Model {model_name} could not be found.")


def get_or_create_scenario(session: sa_Session, scenario_name: str, minutes: int, model_id: int) -> Scenario:
    """
    Returns the scenario if it exists, otherwise creates a new one.

    :param session: SQLAlchemy session in which the database is manipulated.
    :param scenario_name: Name of the scenario to be created.
    :param minutes: Number of minutes of the simulation, needed for the scenario to be created.
    :param model_id: ID of the model to be created.

    :return: The Scenario created or found.
    """

    while True:
        try:
            with session.begin_nested():
                scenario: Scenario | None = session.query(Scenario).filter_by(
                    scenario_name=scenario_name,
                    model_id=model_id
                ).with_for_update().one_or_none()

                if scenario is None:
                    scenario = Scenario(scenario_name=scenario_name, minutes=minutes, model_id=model_id)
                    session.add(scenario)
                    logging.info(f"Scenario '{scenario_name}' created for model {model_id}.")

                    session.flush()  # Ensure that the IntegrityError can be caught
                else:
                    logging.info(f"Scenario '{scenario_name}' already exists for model {model_id}.")

                return scenario

        except IntegrityError:
            logging.warning(
                f"IntegrityError when trying to create scenario '{scenario_name}' for model {model_id}, retrying..."
            )
            session.rollback()

            scenario = session.query(Scenario).filter_by(
                scenario_name=scenario_name,
                model_id=model_id
            ).one_or_none()
            if scenario:
                return scenario
            else:
                raise SQLAlchemyError(f"Scenario {scenario_name} could not be found.")



def connect_to_db() -> Engine | None:
    """
    Attempt to connect to the database and return the engine if successful.

    :return: The Engine object if successful, otherwise None.
    """
    try:
        # Validate configuration before attempting to connect
        validate_db_config()

        # Create the database URL
        db_url = f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine: Engine = create_engine(db_url)

        # Test the connection
        connection = engine.connect()
        logging.info("Connection to Database successful")
        connection.close()
        return engine
    except ValueError as ve:
        logging.error(f"Configuration Error: {ve}")
        return None
    except OperationalError as oe:
        logging.error(f"Database connection failed: {oe}")
        return None
    except Exception as e:
        logging.exception(f"An unexpected error occurred {e}")
        return None


def create_session(engine: Engine) -> sa_Session | None:
    """
    Create a session for interacting with the database.

    :param engine: SQLAlchemy engine for the database.
    :return: Session object if the engine was created successfully.
    """
    try:
        sa_session_maker = sa_sessionmaker(bind=engine)  # Verwende den Alias korrekt
        session: sa_Session = sa_session_maker()  # Verwende das Alias hier korrekt
        return session
    except Exception as e:
        logging.exception(f"Session creation failed {e}")
        return None



def commit_session(session: sa_Session) -> None:
    """
    Commit the session to the database.

    :param session: SQLAlchemy session in which the database is manipulated.
    """
    try:
        session.commit()
        logging.info("Session commit successful")
    except Exception as e:
        logging.exception(f"Session commit failed {e}")
        session.rollback()
        return None


def get_model_id(session: sa_Session, model_name: str, user_id: int) -> int | None:
    """
    Getter for the model_id.

    :param session: SQLAlchemy session in which the database is manipulated.
    :param model_name: Name of the model to be retrieved.
    :param user_id: User ID of the current user needed for referencing the correct model.

    :return: The model_id of the current model or None if not found.
    """
    try:
        model: Model = session.query(Model).filter_by(model_name=model_name, user_id=user_id).one()
        return model.model_id
    except NoResultFound:
        return None


def get_scenario_id(session: sa_Session, scenario_name: str, model_id: int) -> int | None:
    """
    Return the scenario_id of a scenario if found, or None if not.

    :param session: SQLAlchemy session in which the database is manipulated.
    :param scenario_name: Name of the scenario to be retrieved.
    :param model_id: ID of the model to be retrieved.

    :return: The scenario_id of the current model or None if not found.
    """
    try:
        scenario: Scenario = session.query(Scenario).filter_by(scenario_name=scenario_name, model_id=model_id).one()
        return scenario.scenario_id
    except NoResultFound:
        return None


def get_user_id(session: sa_Session, user_name: str) -> int | None:
    """
    Return the scenario_id of a scenario if found, or None if not.

    :param session: SQLAlchemy session in which the database is manipulated.
    :param user_name: Username of the current user (the one trying to access the database)."""
    try:
        user: HSUser = session.query(HSUser).filter_by(user_name=user_name).one()
        return user.user_id
    except NoResultFound:
        return None


def save_to_db(combined_pivot: pd.DataFrame, local_start_time: datetime, local_end_time: datetime,
               minutes: int, num_replications: int):
    """"
    This method interacts with the database to either retrieve or create a user, model, scenario,
    and simulation, ensuring that none are duplicated. It processes data from a pivot table and inserts
    each row as an entry associated with the newly created or retrieved simulation. All changes are
    committed to the database, with a rollback in case of any errors.

    :param combined_pivot: Pandas dataframe of the simulation parameters containing all data to be inserted into the database.
    :param local_start_time: Start time of the simulation.
    :param local_end_time: End time of the simulation.
    :param minutes: Number of minutes to simulate.
    :param num_replications: Number of replications.
    """
    engine: Engine | None = connect_to_db()

    path: str = os.getenv('CONFIG_PATH')
    parts: list[str] = path.split('/')

    model_name: str = parts[-3]  # Model
    scenario_name: str = parts[-2]  # Scenario
    user_name: str = parts[-5]  # User

    session: sa_Session | None = create_session(engine)
    try:
        lock_id = 12345
        """Advisory Lock, so that only one compute node can write at once"""
        session.execute(text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": lock_id})
        try:

            user_id: int = get_or_create_user(session, user_name)
            """user: HSUser | None = session.query(HSUser).filter_by(user_name=user_name).one_or_none()
            if user is None:
                new_user: HSUser = HSUser(user_name=user_name)
                session.add(new_user)
                session.flush()
                user_id = new_user.user_id
            else:
                user = session.query(HSUser).filter_by(user_name=user_name).one_or_none()
                user_id = user.user_id"""

            get_or_create_model(session, model_name, user_id)

            """model = session.query(Model).filter_by(model_name=model_name, user_id=user_id).one_or_none()
            if model is None:
                new_model = Model(model_name=model_name, user_id=user_id)
                session.add(new_model)
                session.flush()
            else:
                session.query(Model).filter_by(model_name=model_name, user_id=user_id).one_or_none()"""

            user_id = get_user_id(session, user_name)
            model_id = get_model_id(session, model_name, user_id)

            scenario_id: int = get_or_create_scenario(session, scenario_name, minutes, model_id)
            """scenario = session.query(Scenario).filter_by(scenario_name=scenario_name, model_id=model_id).one_or_none()
            if scenario is None:
                new_scenario = Scenario(scenario_name=scenario_name, minutes=minutes, model_id=model_id)
                session.add(new_scenario)
                session.flush()

            else:
                Scenario(scenario_name=scenario_name, minutes=minutes, model_id=model_id)

            scenario_id = get_scenario_id(session, scenario_name, model_id)
            logging.info(f"{scenario_id}")"""

            # Create Simulation
            new_simulation: Simulation = Simulation(local_start_time=local_start_time, local_end_time=local_end_time,
                                                    num_replications=num_replications, scenario_id=scenario_id)
            logging.info("Simulation created")
            session.add(new_simulation)
            session.flush()
            logging.info(f"Scenario_ID:{scenario_id}")

            # Look for the latest simulation_id for a specific scenario
            simulation_id = new_simulation.simulation_id

            # PivotTable entries added to the session

            for index, row in combined_pivot.iterrows():
                pivot_entry = PivotTable(
                    simulation_id=simulation_id,
                    type=str(index[0]),
                    name=str(index[1]),
                    stat=str(index[2]),
                    average=float(row['Average']),
                    minimum=float(row['Minimum']),
                    maximum=float(row['Maximum']),
                    half_width=float(row['Half-Width'])
                )
                session.add(pivot_entry)
            # pivot_table_id += 1  # Increment after each row
            # All PivotTable entries added
            commit_session(session)
        finally:
            session.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id})
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
