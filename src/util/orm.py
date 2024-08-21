from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
import psycopg2

Base = declarative_base()

# User Table
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# User Table
class HSUser(Base):
    __tablename__ = 'HsUser'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(255))
    number_started_simulations = Column(Integer)
    model_id = Column(Integer, ForeignKey('Model.model_id'))

    model = relationship('Model', back_populates='hsuser')

    def __init__(self, user_id, user_name, number_started_simulations, model_id):
        self.user_id = user_id
        self.user_name = user_name
        self.number_started_simulations = number_started_simulations
        self.model_id = model_id

    def __repr__(self):
        return f"({self.user_id}, {self.user_name}, {self.number_started_simulations})"


# Model Table
class Model(Base):
    __tablename__ = 'Model'
    model_id = Column(Integer, primary_key=True)
    model_name = Column(String(255))

    scenarios = relationship('ModelScenario', back_populates='model')
    hsuser = relationship('HSUser', back_populates='model')

    def __init__(self, model_id, model_name):
        self.model_id = model_id
        self.model_name = model_name

    def __repr__(self):
        return f"({self.model_id}, {self.model_name})"


# Scenario Table
class Scenario(Base):
    __tablename__ = 'Scenario'
    scenario_id = Column(Integer, primary_key=True)
    scenario_name = Column(String(255))
    number_in_system = Column(Integer)
    avg_time_in_system = Column(Float(20))
    num_time_in_system = Column(Float(20))
    total_time_in_system = Column(Float(20))
    min_time_in_system = Column(Float(20))
    max_time_in_system = Column(Float(20))
    number_created = Column(Integer)
    number_destroyed = Column(Integer)
    seed = Column(Integer)

    sources = relationship('Source', back_populates='scenario')
    sinks = relationship('Sink', back_populates='scenario')
    servers = relationship('Server', back_populates='scenario')
    connections = relationship('Connection', back_populates='scenario')
    entities = relationship('Entity', back_populates='scenario')
    model_scenarios = relationship('ModelScenario', back_populates='scenario')

    def __init__(self, scenario_id, scenario_name, number_in_system, avg_time_in_system, num_time_in_system,
                 total_time_in_system,
                 min_time_in_system, max_time_in_system, number_created, number_destroyed, seed):
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.number_in_system = number_in_system
        self.avg_time_in_system = avg_time_in_system
        self.num_time_in_system = num_time_in_system
        self.total_time_in_system = total_time_in_system
        self.min_time_in_system = min_time_in_system
        self.max_time_in_system = max_time_in_system
        self.number_created = number_created
        self.number_destroyed = number_destroyed
        self.seed = seed

    def __repr__(self):
        return f"({self.scenario_id}, {self.scenario_name})"


# ModelScenario Table (Composite Key)
class ModelScenario(Base):
    __tablename__ = 'Model_Scenario'
    model_id = Column(Integer, ForeignKey('Model.model_id'), primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)

    model = relationship('Model', back_populates='scenarios')
    scenario = relationship('Scenario', back_populates='model_scenarios')

    def __init__(self, model_id, scenario_id):
        self.model_id = model_id
        self.scenario_id = scenario_id

    def __repr__(self):
        return f"({self.model_id}, {self.scenario_id})"


# Source Table
class Source(Base):
    __tablename__ = 'Source'
    source_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    source_name = Column(String(255))
    number_created = Column(Integer)
    number_exited = Column(Integer)
    creation_time_distribution_with_parameters = Column(Float(20))

    scenario = relationship('Scenario', back_populates='sources')

    def __init__(self, source_id, scenario_id, source_name, number_created, number_exited,
                 creation_time_distribution_with_parameters):
        self.source_id = source_id
        self.scenario_id = scenario_id
        self.source_name = source_name
        self.number_created = number_created
        self.number_exited = number_exited
        self.creation_time_distribution_with_parameters = creation_time_distribution_with_parameters

    def __repr__(self):
        return f"({self.source_id}, {self.scenario_id}, {self.source_name})"


# Server Table
class Server(Base):
    __tablename__ = 'Server'
    server_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    server_name = Column(String(255))
    scheduled_utilization = Column(Float(10))
    units_utilized = Column(Integer)
    avg_time_processing = Column(Float(10))
    total_time_processing = Column(Float(10))
    number_entered = Column(Integer)
    number_exited = Column(Integer)
    number_downtimes = Column(Integer)
    processing_time_distribution_with_parameters = Column(Float(20))
    time_between_maschine_breakdowns = Column(Float(20))
    maschine_breakdown_duration = Column(Float(20))
    entities_processed = Column(Integer)
    total_uptime = Column(Float(20))
    number_uptimes = Column(Integer)

    scenario = relationship('Scenario', back_populates='servers')

    def __init__(self, server_id, scenario_id, server_name, scheduled_utilization, units_utilized, avg_time_processing,
                 total_time_processing, number_entered, number_exited, number_downtimes,
                 processing_time_distribution_with_parameters,
                 time_between_maschine_breakdowns, maschine_breakdown_duration, entities_processed, total_uptime,
                 number_uptimes):
        self.server_id = server_id
        self.scenario_id = scenario_id
        self.server_name = server_name
        self.scheduled_utilization = scheduled_utilization
        self.units_utilized = units_utilized
        self.avg_time_processing = avg_time_processing
        self.total_time_processing = total_time_processing
        self.number_entered = number_entered
        self.number_exited = number_exited
        self.number_downtimes = number_downtimes
        self.processing_time_distribution_with_parameters = processing_time_distribution_with_parameters
        self.time_between_maschine_breakdowns = time_between_maschine_breakdowns
        self.maschine_breakdown_duration = maschine_breakdown_duration
        self.entities_processed = entities_processed
        self.total_uptime = total_uptime
        self.number_uptimes = number_uptimes

    def __repr__(self):
        return f"({self.server_id}, {self.scenario_id}, {self.server_name})"


# Sink Table
class Sink(Base):
    __tablename__ = 'Sink'
    sink_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    sink_name = Column(String(255))
    entities_processed = Column(Integer)
    total_time_in_system = Column(Float(20))
    number_entered = Column(Integer)
    max_time_in_system = Column(Float(20))
    min_time_in_system = Column(Float(20))

    scenario = relationship('Scenario', back_populates='sinks')

    def __init__(self, sink_id, scenario_id, sink_name, entities_processed, total_time_in_system, number_entered,
                 max_time_in_system, min_time_in_system):
        self.sink_id = sink_id
        self.scenario_id = scenario_id
        self.sink_name = sink_name
        self.entities_processed = entities_processed
        self.total_time_in_system = total_time_in_system
        self.number_entered = number_entered
        self.max_time_in_system = max_time_in_system
        self.min_time_in_system = min_time_in_system

    def __repr__(self):
        return f"({self.sink_id}, {self.scenario_id}, {self.sink_name})"


# Connection Table
class Connection(Base):
    __tablename__ = 'Connection'
    connection_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    connection_name = Column(String(255))
    entities_processed = Column(Integer)
    number_entered = Column(Integer)
    processing_duration = Column(Float(20))
    probability = Column(Float(20))

    scenario = relationship('Scenario', back_populates='connections')

    def __init__(self, connection_id, scenario_id, connection_name, entities_processed, number_entered,
                 processing_duration,
                 probability):
        self.connection_id = connection_id
        self.scenario_id = scenario_id
        self.connection_name = connection_name
        self.entities_processed = entities_processed
        self.number_entered = number_entered
        self.processing_duration = processing_duration
        self.probability = probability

    def __repr__(self):
        return f"({self.connection_id}, {self.scenario_id}, {self.connection_name})"


# Entity Table
class Entity(Base):
    __tablename__ = 'Entity'
    entity_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    entity_name = Column(String(255))
    creation_time = Column(Float(20))

    scenario = relationship('Scenario', back_populates='entities')

    def __init__(self, entity_id, scenario_id, entity_name, creation_time):
        self.entity_id = entity_id
        self.scenario_id = scenario_id
        self.entity_name = entity_name
        self.creation_time = creation_time

    def __repr__(self):
        return f"({self.entity_id}, {self.scenario_id}, {self.entity_name})"

# Kann genutzt werden um die Tabellen anzulegen
def create_tables():
    db_user = 'sep'
    db_host = 'imt-sep-001.lin.hs-osnabrueck.de'
    db_port = '55432'
    db_name = 'distributed_computing'

    db_url = f"postgresql+psycopg2://{db_user}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
