from tokenize import String

from sqlalchemy import Integer, Column, ForeignKey, Time, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# Klasse, entspricht einer Tabelle in der Datenbank
class Model(Base):
    __tablename__ = 'model'

    modell_id = Column('modell_id', Integer, primary_key=True)
    name = Column('name', String)
    # Konstruktor
    def __init__(self, modell_id, name):
        self.modell_id = modell_id
        self.name = name
    # Methode zum Anzeigen der Objekte
    def __repr__(self):
        return f"({self.modell_id}, {self.name})"


class Szenario(Base):
    __tablename__ = 'scenario'

    scenario_id = Column('scenario_id', Integer, primary_key=True)
    scenario_name = Column('scenario_name', String)
    replication = Column('replication', Integer)
    status = Column('status', Integer)
    seed = Column('seed', Integer)
    modell_id = Column('modell_id', Integer, ForeignKey('model.modell_id'))

    def __init__(self, scenario_id, scenario_name, replication, status, seed, modell_id):
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.replication = replication
        self.status = status
        self.seed = seed
        self.modell_id = modell_id

    def __repr__(self):
        return f"({self.scenario_id}, {self.scenario_name}, {self.replication}, {self.status})"


class Source(Base):
    __tablename__ = 'source'
    source_id = Column('source_id', Integer, primary_key=True)
    name = Column('name', String)
    creation_time_dwp = Column('creation_time_dwp', Time)
    entities_created = Column('entities_created', Integer)
    number_exited = Column('number_exited', Integer)
    scenario_id = Column('scenario_id', Integer, ForeignKey('scenario.scenario_id'))

    def __init__(self, source_id, name, creation_time_dwp, entities_created, number_exited, scenario_id):
       self.source_id = source_id
       self.name = name
       self.creation_time_dwp = creation_time_dwp
       self.entities_created = entities_created
       self.number_exited = number_exited
       self.scenario_id = scenario_id

    def __repr__(self):
        return f"({self.source_id}, {self.name}, {self.creation_time_dwp})"


class Sink(Base):
    __tablename__ = 'sink'

    sink_id = Column('sink_id', Integer, primary_key=True)
    name = Column('name', String)
    entities_processed = Column('entities_processed', Integer)
    total_time_in_system = Column('total_time_in_system', Time)
    min_time_in_system = Column('min_time_in_system', Time)
    number_entered = Column('number_entered', Integer)
    scenario_id = Column('scenario_id', Integer, ForeignKey('scenario.scenario_id'))

    def __init___(self, sink_id, name, entities_processed, total_time_in_system, min_time_in_system, number_entered, scenario_id):
        self.sink_id = sink_id
        self.name = name
        self.entities_processed = entities_processed
        self.total_time_in_system = total_time_in_system
        self.min_time_in_system = min_time_in_system
        self.number_entered = number_entered
        self.scenario_id = scenario_id

    def __repr__(self):
        return f"({self.sink_id}, {self.name}, {self.entities_processed})"

class Server(Base):
    __tablename__ = 'server'

    server_id = Column('server_id', Integer, primary_key=True)
    name = Column('name', String)
    processing_time_dwp = Column('processing_time_dwp', Time)
    time_between_maschine_breakdowns = Column('time_between_maschine_breakdowns', Time)
    maschine_breakdown_duration = Column('maschine_breakdown_duration', Time)
    entities_processed = Column('entities_processed', Integer)
    total_processing_time = Column('total_processing_time', Time)
    number_entered = Column('number_entered', Integer)
    number_exited = Column('number_exited', Integer)
    units_allocated = Column('units_allocated', Integer)
    units_utilized = Column('units_utilized', Integer)
    start_processing_time = Column('start_processing_time', TIMESTAMP)
    total_downtime = Column('total_downtime', Time)
    number_downtime = Column('number_downtime', Integer)
    uptime = Column('uptime', Time)
    total_uptime = Column('total_uptime', Time)
    number_uptimes = Column('number_uptimes', Integer)
    queue_order_id = Column('queue_order_id', Integer, ForeignKey('queue.queue_order_id'))
    scenario_id = Column('scenario_id', Integer, ForeignKey('scenario.scenario_id'))

    def __init__(self, server_id, name, processing_time_dwp, time_between_maschine_breakdowns, maschine_breakdown_duration, entities_processed, total_processing_time, number_entered,
                 number_exited, units_allocated, units_utilized, start_processing_time, total_downtime,
                 number_downtime, uptime, total_uptime, number_uptimes, queue_order_id, scenario_id ):
        self.server_id = server_id
        self.name = name
        self.processing_time_dwp = processing_time_dwp
        self.time_between_maschine_breakdowns = time_between_maschine_breakdowns
        self.maschine_breakdown_duration = maschine_breakdown_duration
        self.entities_processed = entities_processed
        self.total_processing_time = total_processing_time
        self.number_entered = number_entered
        self.number_exited = number_exited
        self.units_allocated = units_allocated
        self.units_utilized = units_utilized
        self.start_processing_time = start_processing_time
        self.total_downtime = total_downtime
        self.number_downtime = number_downtime
        self.uptime = uptime
        self.total_uptime = total_uptime
        self.number_uptimes = number_uptimes
        self.queue_order_id = queue_order_id
        self.scenario_id = scenario_id

    def __repr__(self):
        return f"({self.server_id}, {self.name}, {self.uptime})"

class Path(Base):
    __tablename__ = 'path'

    path_id = Column('path_id', Integer, primary_key=True)
    name = Column('name', String)
    length = Column('length', Integer)
    scenario_id = Column('scenario_id', Integer, ForeignKey('scenario.scenario_id'))

    def __init__(self, path_id, name, length, scenario_id):
        self.path_id = path_id
        self.name = name
        self.length = length


    def __repr__(self):
        return f"({self.path_id, self.name, self.length})"

class QueueOrder(Base):
    __tablename__ = 'queue_order'

    queue_order_id = Column('queue_order_id', Integer, primary_key=True)
    procedure = Column('procedure', String)

    def __init__(self, queue_order_id, procedure):
        self.queue_order_id = queue_order_id
        self.procedure = procedure

    def __repr__(self):
        return f"({self.queue_order_id, self.procedure})"

class Entity(Base):
    __tablename__ = 'entity'

    entity_id = Column('entity_id', Integer, primary_key=True)
    name = Column('name', String)
    creation_time = Column('creation_time', Time)
    destruction_time = Column('destruction_time', Time)
    source_id = Column('source_id', Integer, ForeignKey('source.source_id'))

    def __init__ (self, entity_id, name, creation_time, destruction_time, source_id):
        self.entity_id = entity_id
        self.name = name
        self.creation_time = creation_time
        self.destruction_time = destruction_time
        self.source_id = source_id

    def __repr__(self):
        return f"({self.entity_id, self.name, self.creation_time})"




