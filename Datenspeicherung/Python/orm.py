from sqlalchemy import Column, ForeignKey, Integer, String, Float, TIMESTAMP, create_engine, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class HSUser(Base):
    __tablename__ = 'HSUser'
    user_id = Column(Integer, primary_key=True, nullable=False)
    user_name = Column(String(255), nullable=False)
    number_started_simulations = Column(Integer)
    models = relationship('Model', back_populates='hsuser', cascade="all, delete-orphan")


class Model(Base):
    __tablename__ = 'Model'
    model_id = Column(Integer, primary_key=True, nullable=False)
    model_name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('HSUser.user_id'), nullable=False)
    hsuser = relationship('HSUser', back_populates='models')
    scenarios = relationship('Scenario', back_populates='model', cascade="all, delete-orphan")


class Scenario(Base):
    __tablename__ = 'Scenario'
    scenario_id = Column(Integer, primary_key=True, nullable=False)
    scenario_name = Column(String(255))
    number_in_system = Column(Integer)
    avg_time_in_system = Column(Float)
    max_time_in_system = Column(Float)
    min_time_in_system = Column(Float)
    number_created = Column(Integer)
    number_destroyed = Column(Integer)
    seed = Column(Integer)
    model_id = Column(Integer, ForeignKey('Model.model_id'), nullable=False)
    model = relationship('Model', back_populates='scenarios')
    sources = relationship('Source', back_populates='scenario', cascade="all, delete-orphan")
    sinks = relationship('Sink', back_populates='scenario', cascade="all, delete-orphan")
    servers = relationship('Server', back_populates='scenario', cascade="all, delete-orphan")
    connections = relationship('Connection', back_populates='scenario', cascade="all, delete-orphan")
    entities = relationship('Entity', back_populates='scenario', cascade="all, delete-orphan")
    simulations = relationship('Simulation', back_populates='scenario', cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = 'Source'
    source_id = Column(Integer, primary_key=True, nullable=False)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), nullable=False)
    source_name = Column(String(255))
    number_created = Column(Integer)
    number_exited = Column(Integer)
    creation_time_distribution_with_parameters = Column(Float)

    scenario = relationship('Scenario', back_populates='sources')


class Server(Base):
    __tablename__ = 'Server'
    server_id = Column(Integer, primary_key=True, nullable=False)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), nullable=False)
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
    __tablename__ = 'Sink'
    sink_id = Column(Integer, primary_key=True, nullable=False)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), nullable=False)
    sink_name = Column(String(255))
    entities_processed = Column(Integer)
    total_time_in_system = Column(Float)
    number_entered = Column(Integer)
    max_time_in_system = Column(Float)
    min_time_in_system = Column(Float)

    scenario = relationship('Scenario', back_populates='sinks')


class Connection(Base):
    __tablename__ = 'Connection'
    connection_id = Column(Integer, primary_key=True, nullable=False)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), nullable=False)
    connection_name = Column(String(255))
    entities_processed = Column(Integer)
    number_entered = Column(Integer)
    processing_duration = Column(Float)
    availability = Column(Float)

    scenario = relationship('Scenario', back_populates='connections')


class Entity(Base):
    __tablename__ = 'Entity'
    entity_id = Column(Integer, primary_key=True, nullable=False)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), nullable=False)
    entity_name = Column(String(255))
    creation_time = Column(Float)

    scenario = relationship('Scenario', back_populates='entities')


class PivotTable(Base):
    __tablename__ = 'Pivot_Table'
    pivot_table_id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(Integer, ForeignKey('Simulation.simulation_id'), nullable=False)
    type = Column(String(255))
    name = Column(String(255))
    stat = Column(String(255))
    average = Column(Float)
    minimum = Column(Float)
    maximum = Column(Float)
    half_width = Column(Float)


class Simulation(Base):
    __tablename__ = 'Simulation'
    simulation_id = Column(Integer, primary_key=True, nullable=False)
    local_start_time = Column(TIMESTAMP)
    local_end_time = Column(TIMESTAMP)
    scenario_id = Column(Integer, ForeignKey('Scenario.scenario_id'), nullable=False)

    scenario = relationship('Scenario', back_populates='simulations')


def create_tables():
    db_user = 'sep'
    db_host = 'imt-sep-001.lin.hs-osnabrueck.de'
    db_port = '55432'
    db_name = 'distributed_computing'
    db_password = 'sep'

    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)


create_tables()
