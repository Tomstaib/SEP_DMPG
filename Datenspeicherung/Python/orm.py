from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
import psycopg2

Base = declarative_base()

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# HSUser Table
class HSUser(Base):
    __tablename__ = 'HSUser'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(255))
    number_started_simulations = Column(Integer)

    models = relationship('Model', back_populates='hsuser')


# Model Table
class Model(Base):
    __tablename__ = 'Model'
    model_id = Column(Integer, primary_key=True)
    model_name = Column(String(255))
    user_id = Column(Integer, ForeignKey('HSUser.user_id'))

    hsuser = relationship('HSUser', back_populates='models')
    model_scenarios = relationship('ModelScenario', back_populates='model')


# Scenario Table
class Scenario(Base):
    __tablename__ = 'Scenario'
    scenario_id = Column(Integer, primary_key=True)
    scenario_name = Column(String(255))
    number_in_system = Column(Integer)
    avg_time_in_system = Column(Float)
    max_time_in_system = Column(Float)
    min_time_in_system = Column(Float)
    number_created = Column(Integer)
    number_destroyed = Column(Integer)
    seed = Column(Integer)

    sources = relationship('Source', back_populates='scenario')
    sinks = relationship('Sink', back_populates='scenario')
    servers = relationship('Server', back_populates='scenario')
    connections = relationship('Connection', back_populates='scenario')
    entities = relationship('Entity', back_populates='scenario')
    model_scenarios = relationship('ModelScenario', back_populates='scenario')


# ModelScenario Table
class ModelScenario(Base):
    __tablename__ = 'Model_Scenario'
    model_id = Column(Integer, ForeignKey('Model.model_id'), primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)

    model = relationship('Model', back_populates='model_scenarios')
    scenario = relationship('Scenario', back_populates='model_scenarios')


# Source Table
class Source(Base):
    __tablename__ = 'Source'
    source_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    source_name = Column(String(255))
    number_created = Column(Integer)
    number_exited = Column(Integer)
    creation_time_distribution_with_parameters = Column(Float)

    scenario = relationship('Scenario', back_populates='sources')


# Server Table
class Server(Base):
    __tablename__ = 'Server'
    server_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    server_name = Column(String(255))
    scheduled_utilization = Column(Float)
    units_utilized = Column(Integer)
    avg_time_processing = Column(Float)
    total_time_processing = Column(Float)
    number_entered = Column(Integer)
    number_exited = Column(Integer)
    number_downtimes = Column(Integer)
    total_downtime = Column(Float)
    processing_time_distribution_with_parameters = Column(Float)
    time_between_maschine_breakdowns = Column(Float)
    maschine_breakdown_duration = Column(Float)
    entities_processed = Column(Integer)
    total_uptime = Column(Float)
    number_uptimes = Column(Integer)

    scenario = relationship('Scenario', back_populates='servers')


# Sink Table
class Sink(Base):
    __tablename__ = 'Sink'
    sink_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    sink_name = Column(String(255))
    entities_processed = Column(Integer)
    total_time_in_system = Column(Float)
    number_entered = Column(Integer)
    max_time_in_system = Column(Float)
    min_time_in_system = Column(Float)

    scenario = relationship('Scenario', back_populates='sinks')


# Connection Table
class Connection(Base):
    __tablename__ = 'Connection'
    connection_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    connection_name = Column(String(255))
    entities_processed = Column(Integer)
    number_entered = Column(Integer)
    processing_duration = Column(Float)
    availability = Column(Float)

    scenario = relationship('Scenario', back_populates='connections')


# Entity Table
class Entity(Base):
    __tablename__ = 'Entity'
    entity_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    entity_name = Column(String(255))
    creation_time = Column(Float)

    scenario = relationship('Scenario', back_populates='entities')


# Kann genutzt werden um die Tabellen anzulegen
def create_tables():
    db_user = 'sep'
    db_host = 'localhost'
    db_port = '5432'
    db_name = 'distributed_computing'
    db_password = 'sep'

    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

create_tables()
