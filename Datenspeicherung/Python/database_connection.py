import logging
import sys
import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
import orm
from sqlalchemy.exc import OperationalError, SQLAlchemyError, NoResultFound

DB_USER = 'sep'
DB_HOST = 'imt-sep-001.lin.hs-osnabrueck.de'
DB_PORT = '55432'
DB_NAME = 'distributed_computing'
DB_PASSWORD = 'oishooX2iefeiNai'

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO)


def validate_db_config():
    """Validate that all necessary database configuration variables are set."""
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        raise ValueError("Database configuration is incomplete. Please check all required fields.")


def get_next_pivot_table_id(session: Session) -> int:
    """Return the next pivot table id"""
    try:
        highest_id = session.query(func.max(orm.PivotTable.pivot_table_id)).scalar()
    except Exception as e:
        print(f"Failed to reach next pivot table ID: {e}")
        return 1

    """If there are no simulation ids yet, return the highest pivot table id"""
    if highest_id is None:
        return 1
    return highest_id + 1


def get_or_create_user(session, user_name) -> int:
    # Search vor a user, if not found it will be created
    try:
        user = session.query(orm.HSUser).filter(orm.HSUser.user_name == user_name).one()
        return user.user_id
    except NoResultFound:
        # No user found
        new_user = orm.HSUser(user_name=user_name)
        session.add(new_user)
        commit_session(session)
        return new_user.user_id


def connect_to_db():
    """Attempt to connect to the database and return the engine if successful."""
    try:
        # Validate configuration before attempting to connect
        validate_db_config()

        # Create the database URL
        db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
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
        logging.info("Data saved in database")
    except Exception as e:
        logging.exception("Session commit failed")
        session.rollback()
        logging.exception("Session rollback failed")
        return None


# Creating the database scheme from orm.py
def main():
    """Main function to connect to the database and create the database scheme"""
    # Attempt to connect to the database
    engine = connect_to_db()
    if engine:
        try:
            # Create the tables if the connection was successful
            orm.create_tables()
            logging.info("Tables created")
        except SQLAlchemyError as se:
            logging.exception("Failed to create tables")
            return  # Optional: Return or exit on critical error

        # Create a session
        session = create_session(engine)
        if session:
            try:
                # Commit session
                session.commit()
                logging.info("Session committed successfully")
            except SQLAlchemyError as se:
                session.rollback()
                logging.error(f"Failed to commit session: {se}")
            except Exception as e:
                session.rollback()
                logging.exception("An unexpected error occurred during session commit")
            finally:
                session.close()
        else:
            # Case: No session available
            logging.error("Failed to create session.")
    else:
        logging.error("Failed to connect to the database")


# Ensure main() is called only when this script is executed directly
if __name__ == "__main__":
    main()
