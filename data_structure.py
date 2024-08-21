from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# User Table
class User(Base):
    __tablename__ = 'User'
    UserID = Column(Integer, primary_key=True)
    UserName = Column(String(255))
    NumberStartedSimulations = Column(Integer)
    ModelID = Column(Integer, ForeignKey('Model.ModelID'))

    model = relationship('Model', back_populates='users')


# Model Table
class Model(Base):
    __tablename__ = 'Model'
    ModelID = Column(Integer, primary_key=True)
    ModelName = Column(String(255))

    scenarios = relationship('ModelScenario', back_populates='model')
    users = relationship('User', back_populates='model')


# Scenario Table
class Scenario(Base):
    __tablename__ = 'Scenario'
    ScenarioID = Column(Integer, primary_key=True)
    ScenarioName = Column(String(255))
    NumberInSystem = Column(Integer)
    AvgTimeInSystem = Column(Float(20))
    NumTimeInSystem = Column(Float(20))
    TotalTimeInSystem = Column(Float(20))
    MinTimeInSystem = Column(Float(20))
    MaxTimeInSystem = Column(Float(20))
    NumberCreated = Column(Integer)
    NumberDestroyed = Column(Integer)
    Seed = Column(Integer)

    sources = relationship('Source', back_populates='scenario')
    sinks = relationship('Sink', back_populates='scenario')
    servers = relationship('Server', back_populates='scenario')
    connections = relationship('Connection', back_populates='scenario')
    entities = relationship('Entity', back_populates='scenario')
    model_scenarios = relationship('ModelScenario', back_populates='scenario')


# ModelScenario Table (Composite Key)
class ModelScenario(Base):
    __tablename__ = 'Model_Scenario'
    ModelID = Column(Integer, ForeignKey('Model.ModelID'), primary_key=True)
    ScenarioID = Column(Integer, ForeignKey('Scenario.ScenarioID'), primary_key=True)

    model = relationship('Model', back_populates='scenarios')
    scenario = relationship('Scenario', back_populates='model_scenarios')


# Source Table
class Source(Base):
    __tablename__ = 'Source'
    SourceID = Column(Integer, primary_key=True)
    ScenarioID = Column(Integer, ForeignKey('Scenario.ScenarioID'), primary_key=True)
    SourceName = Column(String(255))
    NumberCreated = Column(Integer)
    NumberExited = Column(Integer)
    CreationTimeDistributionWithParameters = Column(Float(20))

    scenario = relationship('Scenario', back_populates='sources')


# Server Table
class Server(Base):
    __tablename__ = 'Server'
    ServerID = Column(Integer, primary_key=True)
    ScenarioID = Column(Integer, ForeignKey('Scenario.ScenarioID'), primary_key=True)
    ServerName = Column(String(255))
    ScheduledUtilization = Column(Float(10))
    UnitsUtilized = Column(Integer)
    AvgTimeProcessing = Column(Float(10))
    TotalTimeProcessing = Column(Float(10))
    NumberEntered = Column(Integer)
    NumberExited = Column(Integer)
    NumberDowntimes = Column(Integer)
    ProcessingTimeDistributionWithParameters = Column(Float(20))
    TimeBetweenMaschineBreakdowns = Column(Float(20))
    MaschineBreakdownDuration = Column(Float(20))
    EntitiesProcessed = Column(Integer)
    TotalUptime = Column(Float(20))
    NumberUptimes = Column(Integer)

    scenario = relationship('Scenario', back_populates='servers')


# Sink Table
class Sink(Base):
    __tablename__ = 'Sink'
    SinkID = Column(Integer, primary_key=True)
    ScenarioID = Column(Integer, ForeignKey('Scenario.ScenarioID'), primary_key=True)
    SinkName = Column(String(255))
    EntitiesProcessed = Column(Integer)
    TotalTimeInSystem = Column(Float(20))
    NumberEntered = Column(Integer)
    MaxTimeInSystem = Column(Float(20))
    MinTimeInSystem = Column(Float(20))

    scenario = relationship('Scenario', back_populates='sinks')


# Connection Table
class Connection(Base):
    __tablename__ = 'Connection'
    ConnectionID = Column(Integer, primary_key=True)
    ScenarioID = Column(Integer, ForeignKey('Scenario.ScenarioID'), primary_key=True)
    ConnectionName = Column(String(255))
    EntitiesProcessed = Column(Integer)
    NumberEntered = Column(Integer)
    ProcessingDuration = Column(Float(20))
    Probability = Column(Float(20))

    scenario = relationship('Scenario', back_populates='connections')


# Entity Table
class Entity(Base):
    __tablename__ = 'Entity'
    EntityID = Column(Integer, primary_key=True)
    ScenarioID = Column(Integer, ForeignKey('Scenario.ScenarioID'), primary_key=True)
    EntityName = Column(String(255))
    CreationTime = Column(Float(20))

    scenario = relationship('Scenario', back_populates='entities')
