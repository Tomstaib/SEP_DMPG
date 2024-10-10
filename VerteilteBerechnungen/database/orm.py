import logging
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Float, TIMESTAMP, create_engine, UniqueConstraint
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, relationship, Session


from VerteilteBerechnungen.database.database_params import DB_USER, DB_HOST, DB_PORT, DB_NAME


Base = declarative_base()
"""Base class for ORM models"""


class HSUser(Base):
    """
    Class for User. Needed for referencing the correct Models, Scenario etc.
    """
    __tablename__ = 'HSUser'
    user_id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_name: str = Column(String(255))
    models = relationship('Model', back_populates='hsuser', cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('user_name', name='unique_user_name'),)  # Unique username in database


class Model(Base):
    """
    Class for the Model. A Model is a combination objects.
    """
    __tablename__ = 'Model'
    model_id: int = Column(Integer, primary_key=True, autoincrement=True)
    model_name: str = Column(String(255), nullable=False)
    user_id: int = Column(Integer, ForeignKey('HSUser.user_id', ondelete="CASCADE"))
    hsuser = relationship('HSUser', back_populates='models')
    scenarios = relationship('Scenario', back_populates='model', cascade="all, delete-orphan")


class Scenario(Base):
    """
    Class for the Scenario. A Scenario is inside a model.
    """
    __tablename__ = 'Scenario'
    scenario_id: int = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    scenario_name: str = Column(String(255))
    number_in_system: int = Column(Integer)
    avg_time_in_system: float = Column(Float)
    max_time_in_system: float = Column(Float)
    min_time_in_system: float = Column(Float)
    number_created: int = Column(Integer)
    number_destroyed: int = Column(Integer)
    minutes: float = Column(Float)
    seed: int = Column(Integer)
    model_id: int = Column(Integer, ForeignKey('Model.model_id', ondelete="CASCADE"))
    model = relationship('Model', back_populates='scenarios')
    sources = relationship('Source', back_populates='scenario', cascade="all, delete-orphan")
    sinks = relationship('Sink', back_populates='scenario', cascade="all, delete-orphan")
    servers = relationship('Server', back_populates='scenario', cascade="all, delete-orphan")
    connections = relationship('Connection', back_populates='scenario', cascade="all, delete-orphan")
    entities = relationship('Entity', back_populates='scenario', cascade="all, delete-orphan")
    simulations = relationship('Simulation', back_populates='scenario', cascade="all, delete-orphan")


class Source(Base):
    """
    Class for the Source. A Source emits entities.
    """
    __tablename__ = 'Source'
    source_id: int = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id: int = Column(Integer, ForeignKey('Scenario.scenario_id', ondelete="CASCADE"))
    source_name: str = Column(String(255))
    number_created: int = Column(Integer)
    number_exited: int = Column(Integer)
    creation_time_distribution_with_parameters: float = Column(Float)

    scenario = relationship('Scenario', back_populates='sources')


class Server(Base):
    """
    Class for the Server. A Server processes entities.
    """
    __tablename__ = 'Server'
    server_id: int = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id: int = Column(Integer, ForeignKey('Scenario.scenario_id', ondelete="CASCADE"))
    server_name: str = Column(String(255))
    scheduled_utilization: float = Column(Float)
    units_utilized: int = Column(Integer)
    avg_time_processing: float = Column(Float)
    total_time_processing: float = Column(Float)
    number_entered: int = Column(Integer)
    number_exited: int = Column(Integer)
    number_downtimes: int = Column(Integer)
    total_downtime: float = Column(Float)
    processing_time_distribution_with_parameters: float = Column(Float)
    time_between_machine_breakdowns: float = Column(Float)
    machine_breakdown_duration: float = Column(Float)
    entities_processed: int = Column(Integer)
    total_uptime: float = Column(Float)
    number_uptimes: int = Column(Integer)

    scenario = relationship('Scenario', back_populates='servers')


class Sink(Base):
    """
    Class for the Sink.
    """
    __tablename__ = 'Sink'
    sink_id: int = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id: int = Column(Integer, ForeignKey('Scenario.scenario_id', ondelete="CASCADE"))
    sink_name: str = Column(String(255))
    entities_processed: int = Column(Integer)
    total_time_in_system: float = Column(Float)
    number_entered: int = Column(Integer)
    max_time_in_system: float = Column(Float)
    min_time_in_system: float = Column(Float)

    scenario = relationship('Scenario', back_populates='sinks')


class Connection(Base):
    """
    Class for the Connection. A Connection connects to simulation components.
    """
    __tablename__ = 'Connection'
    connection_id: int = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id: int = Column(Integer, ForeignKey('Scenario.scenario_id', ondelete="CASCADE"))
    connection_name: str = Column(String(255))
    entities_processed: int = Column(Integer)
    number_entered: int = Column(Integer)
    processing_duration: float = Column(Float)
    availability: float = Column(Float)

    scenario = relationship('Scenario', back_populates='connections')


class Entity(Base):
    """
    Class for the Entity.
    """
    __tablename__ = 'Entity'
    entity_id: int = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id: int = Column(Integer, ForeignKey('Scenario.scenario_id', ondelete="CASCADE"))
    entity_name: str = Column(String(255))
    creation_time: float = Column(Float)

    scenario = relationship('Scenario', back_populates='entities')


class PivotTable(Base):
    """
    Class for the PivotTable. The PivotTable stores the most important simulation results.
    """
    __tablename__ = 'Pivot_Table'
    pivot_table_id: int = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id: int = Column(Integer, ForeignKey('Simulation.simulation_id', ondelete="CASCADE"))
    type: str = Column(String(255))
    name: str = Column(String(255))
    stat: str = Column(String(255))
    average: float = Column(Float)
    minimum: float = Column(Float)
    maximum: float = Column(Float)
    half_width: float = Column(Float)


class Simulation(Base):
    """
    Class for the Simulation. A Simulation is inside a Scenario and simply represents multiple runs.
    """
    __tablename__ = 'Simulation'
    simulation_id: int = Column(Integer, primary_key=True, autoincrement=True)
    local_start_time: datetime = Column(TIMESTAMP)
    local_end_time: datetime = Column(TIMESTAMP)
    num_replications: int = Column(Integer)
    scenario_id: int = Column(Integer, ForeignKey('Scenario.scenario_id', ondelete="CASCADE"))

    scenario = relationship('Scenario', back_populates='simulations')


def create_tables():
    """
    Creates all tables from the classes.
    """
    db_url = f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)


def main():
    """
    Main function to connect to the database and create the database scheme. Starting by making an engine,
    creating the tables, then creating a session and finally commiting.
    """
    from VerteilteBerechnungen.database import database_connection
    
    engine: Engine | None = database_connection.connect_to_db()
    if engine:
        try:
            # Create tables if connection was successful
            create_tables()
            logging.info("Tables created")
        except SQLAlchemyError as se:
            logging.exception(f"Failed to create tables {se}")
            return

        session: Session | None = database_connection.create_session(engine)
        if session:
            try:
                session.commit()
                logging.info("Session committed successfully")
            except SQLAlchemyError as se:
                session.rollback()
                logging.error(f"Failed to commit session: {se}")
            except Exception as e:
                session.rollback()
                logging.exception(f"An unexpected error occurred during session commit {e}")
            finally:
                session.close()
        else:
            # No session available
            logging.error("Failed to create session.")
    else:
        logging.error("Failed to connect to the database")



if __name__ == "__main__":
    main() # pragma: no cover
