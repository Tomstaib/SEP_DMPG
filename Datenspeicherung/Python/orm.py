from sqlalchemy import Column, ForeignKey, Integer, String, Float, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class HSUser(Base):
    __tablename__ = 'HSUser'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(255))
    number_started_simulations = Column(Integer)
    models = relationship('Model', back_populates='hsuser')

class Model(Base):
    __tablename__ = 'Model'
    model_id = Column(Integer, primary_key=True)
    model_name = Column(String(255))
    user_id = Column(Integer, ForeignKey('HSUser.user_id'))
    hsuser = relationship('HSUser', back_populates='models')
    model_scenarios = relationship('ModelScenario', back_populates='model')

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

class ModelScenario(Base):
    __tablename__ = 'Model_Scenario'
    model_id = Column(Integer, ForeignKey('Model.model_id'), primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    model = relationship('Model', back_populates='model_scenarios')
    scenario = relationship('Scenario', back_populates='model_scenarios')

class Source(Base):
    __tablename__ = 'sources'
    source_id = Column(Integer, primary_key=True)  # autoincrement entfernt
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    source_name = Column(String(255))
    number_created = Column(Integer)
    number_exited = Column(Integer)
    creation_time_distribution_with_parameters = Column(Float)

    scenario = relationship('Scenario', back_populates='sources')




class Server(Base):
    __tablename__ = 'servers'
    server_id = Column(Integer, primary_key=True)  # autoincrement hinzugefügt
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
    time_between_machine_breakdowns = Column(Float)
    machine_breakdown_duration = Column(Float)
    entities_processed = Column(Integer)
    total_uptime = Column(Float)
    number_uptimes = Column(Integer)

    scenario = relationship('Scenario', back_populates='servers')


class Sink(Base):
    __tablename__ = 'sinks'
    sink_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    sink_name = Column(String(255))
    entities_processed = Column(Integer)
    total_time_in_system = Column(Float)
    number_entered = Column(Integer)
    max_time_in_system = Column(Float)
    min_time_in_system = Column(Float)

    scenario = relationship('Scenario', back_populates='sinks')


class Connection(Base):
    __tablename__ = 'connections'
    connection_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    connection_name = Column(String(255))
    entities_processed = Column(Integer)
    number_entered = Column(Integer)
    processing_duration = Column(Float)
    availability = Column(Float)

    scenario = relationship('Scenario', back_populates='connections')


class Entity(Base):
    __tablename__ = 'entities'
    entity_id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), primary_key=True)
    entity_name = Column(String(255))
    creation_time = Column(Float)

    scenario = relationship('Scenario', back_populates='entities')


class PivotTable(Base):
    __tablename__ = 'pivot_table'
    id = Column(Integer, primary_key=True)
    type = Column(String(255))
    name = Column(String(255))
    stat = Column(String(255))
    average = Column(Float)
    minimum = Column(Float)
    maximum = Column(Float)
    half_width = Column(Float)


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
