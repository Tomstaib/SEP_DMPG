import logging
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import orm
from sqlalchemy.exc import OperationalError, SQLAlchemyError


DB_USER = 'sep'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'distributed_computing'
DB_PASSWORD = 'sep'

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO)

def validate_db_config():
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        raise ValueError("Database configuration is incomplete. Please check all required fields.")

def connect_to_db():
    try:
        # Validate configuration before attempting to connect
        validate_db_config()

        # Create the database URL
        db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(db_url)

        # Test the connection
        connection = engine.connect()
        logging.info("Connection successful")
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
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        return session
    except Exception as e:
        logging.exception("Session creation failed")
        return None

def main():
    # Versuche, eine Verbindung zur Datenbank herzustellen
    engine = connect_to_db()
    if engine:
        # Erstelle die Tabellen, wenn die Verbindung erfolgreich hergestellt wurde
        orm.create_tables()

        # Erstelle eine Sitzung
        session = create_session(engine)
        if session:
            try:
                ##### Example of how to save data #####
                # model = orm.Model(123, 'Test')
                # session.add(model)

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

                ##### Example of how to retrieve data #####
                # results = session.query(orm.Model).all()
                # print(results)
    else:
        logging.error("Failed to connect to the database")

# Ensure main() is called only when this script is executed directly
if __name__ == "__main__":
   main()
