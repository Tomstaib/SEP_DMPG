import logging
import sys
import os
import numpy as np
import threading

import time
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker, Session

from src.util.orm import PivotTable, Simulation, Scenario, Model, HSUser
from sqlalchemy.exc import OperationalError, SQLAlchemyError, NoResultFound, IntegrityError

DB_USER = 'sep'
DB_HOST = 'imt-sep-001.lin.hs-osnabrueck.de'
DB_PORT = '55432'
DB_NAME = 'distributed_computing'

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO)

lock = threading.Lock()


def validate_db_config():
    """Validate that all necessary database configuration variables are set."""
    if not all([DB_USER, DB_HOST, DB_PORT, DB_NAME]):
        raise ValueError("Database configuration is incomplete. Please check all required fields.")


def get_or_create_user(session: Session, user_name: str) -> int:
    """Returns the user_id of a user if found, or creates a new user if not found"""
    time.sleep(np.random.randint(1, 11))

    with session.no_autoflush:
        user = session.query(HSUser).filter_by(user_name=user_name).one_or_none()
        if user:
            return user.user_id
        else:
            try:
                new_user = HSUser(user_name=user_name)
                session.add(new_user)
                session.flush()
                return new_user.user_id
            except IntegrityError:
                session.rollback()

                user = session.query(HSUser).filter_by(user_name=user_name).one_or_none()
                if user:
                    return user.user_id
                else:
                    raise


def get_or_create_model(session: Session, model_name: str, user_id: int) -> Model:
    """Returns the model_id of a model if found, or creates a new model if not found"""
    while True:
        try:
            time.sleep(np.random.randint(1, 11))
            model = session.query(Model).filter_by(model_name=model_name,
                                                   user_id=user_id).with_for_update().one_or_none()

            if model:
                return model
            else:
                new_model = Model(model_name=model_name, user_id=user_id)
                session.add(new_model)
            session.flush()
            return new_model

        except IntegrityError:
            session.rollback()

            model = session.query(Model).filter_by(model_name=model_name, user_id=user_id).one_or_none()
            if model:
                return model


def get_or_create_scenario(session: Session, scenario_name: str, minutes: int, model_id: int) -> Scenario:
    """Returns the scenario if it exists, otherwise creates a new one"""
    time.sleep(np.random.randint(1, 11))
    with session.begin_nested():
        scenario = session.query(Scenario).filter_by(scenario_name=scenario_name,
                                                     model_id=model_id).with_for_update().one_or_none()

        if scenario is None:
            scenario = Scenario(scenario_name=scenario_name, minutes=minutes, model_id=model_id)
            session.add(scenario)
            logging.info(f"Scenario '{scenario_name}' created for model {model_id}.")
        else:
            logging.info(f"Scenario '{scenario_name}' already exists for model {model_id}.")

        return scenario


def connect_to_db():
    """Attempt to connect to the database and return the engine if successful."""
    try:
        # Validate configuration before attempting to connect
        validate_db_config()

        # Create the database URL
        db_url = f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(db_url)

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
        logging.exception("An unexpected error occurred")
        return None


def create_session(engine):
    """Create a session for interacting with the database."""
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        return session
    except Exception as e:
        logging.exception("Session creation failed")
        return None


def commit_session(session):
    try:
        session.commit()
        logging.info("Session commit successful")
    except Exception as e:
        logging.exception("Session commit failed")
        session.rollback()
        logging.exception("Session rollback failed")
        return None


def main(combined_pivot, local_start_time, local_end_time, minutes, num_replications):
    '''
    This method interacts with the database to either retrieve or create a user, model, scenario,
    and simulation, ensuring that none are duplicated. It processes data from a pivot table and inserts
    each row as an entry associated with the newly created or retrieved simulation. All changes are
    committed to the database, with a rollback in case of any errors.
    '''

    engine = connect_to_db()

    path = os.getenv('CONFIG_PATH')
    parts = path.split('/')

    model_name = parts[-3]  # Model
    scenario_name = parts[-2]  # Scenario
    user_name = parts[-5]  # User

    session = create_session(engine)
    try:
        # Advisory Lock, so that only one compute node can write at once
        lock_id = 12345
        session.execute(text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": lock_id})
        try:

            def get_model_id(session: Session, model_name: str, user_id: int) -> int:
                """To return the model_id of a model is found, or None if not"""
                try:
                    model = session.query(Model).filter_by(model_name=model_name, user_id=user_id).one()
                    return model.model_id
                except NoResultFound:
                    return None

            def get_scenario_id(session: Session, scenario_name: str, model_id: int) -> int:
                """Return the scenario_id of a scenario if found, or None if not."""
                try:
                    scenario = session.query(Scenario).filter_by(scenario_name=scenario_name, model_id=model_id).one()
                    return scenario.scenario_id
                except NoResultFound:
                    return None

            def get_user_id(session: Session, user_name: str) -> int:
                """Return the scenario_id of a scenario if found, or None if not."""
                try:
                    user = session.query(HSUser).filter_by(user_name=user_name).one()
                    return user.user_id
                except NoResultFound:
                    return None

            user = session.query(HSUser).filter_by(user_name=user_name).one_or_none()
            if user is None:
                new_user = HSUser(user_name=user_name)
                session.add(new_user)
                session.flush()
                user_id = new_user.user_id
            else:
                user = session.query(HSUser).filter_by(user_name=user_name).one_or_none()
                user_id = user.user_id

            model = session.query(Model).filter_by(model_name=model_name, user_id=user_id).one_or_none()
            if model is None:
                new_model = Model(model_name=model_name, user_id=user_id)
                session.add(new_model)
                session.flush()
            else:
                session.query(Model).filter_by(model_name=model_name, user_id=user_id).one_or_none()

            user_id = get_user_id(session, user_name)
            model_id = get_model_id(session, model_name, user_id)
            scenario = session.query(Scenario).filter_by(scenario_name=scenario_name, model_id=model_id).one_or_none()
            if scenario is None:
                new_scenario = Scenario(scenario_name=scenario_name, minutes=minutes, model_id=model_id)
                session.add(new_scenario)
                session.flush()

            else:
                Scenario(scenario_name=scenario_name, minutes=minutes, model_id=model_id)

            scenario_id = get_scenario_id(session, scenario_name, model_id)
            logging.info(f"{scenario_id}")
            # Create Simulation
            new_simulation = Simulation(local_start_time=local_start_time, local_end_time=local_end_time,
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
                    # pivot_table_id=pivot_table_id,
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


if __name__ == "__main__":
    main()
