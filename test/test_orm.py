import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Fügt den Pfad des lokalen Moduls für Docker-Container hinzu
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Datenspeicherung/Python')
))

# Import der ORM-Module
import orm
from orm import Base, HSUser, Model, Scenario, Source, Server, Sink, Connection, Entity, PivotTable

# SQLite In-Memory-Datenbank initialisieren
engine = create_engine('sqlite:///:memory:')

# Fixture für das Setup der In-Memory-Datenbank auf Modulebene
@pytest.fixture(scope='module')
def test_engine():
    Base.metadata.create_all(engine)
    return engine

# Fixture für das Zurücksetzen der Datenbank vor jedem Test
@pytest.fixture(scope='function')
def test_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# Testet die Erstellung und Abfrage eines HSUser-Eintrags
def test_create_hsuser(test_session):
    new_user = HSUser(user_name="Test User", number_started_simulations=10)
    test_session.add(new_user)
    test_session.commit()

    fetched_user = test_session.query(HSUser).filter_by(user_name="Test User").first()
    assert fetched_user is not None
    assert fetched_user.number_started_simulations == 10

# Testet die Beziehung zwischen Model und HSUser
def test_create_model_with_user(test_session):
    new_user = HSUser(user_name="Test User 2", number_started_simulations=5)
    new_model = Model(model_name="Test Model", hsuser=new_user)
    
    test_session.add(new_model)
    test_session.commit()

    fetched_model = test_session.query(Model).filter_by(model_name="Test Model").first()
    assert fetched_model is not None
    assert fetched_model.hsuser.user_name == "Test User 2"

# Integrationstest: Testet die Beziehung zwischen Scenario und Source
def test_create_scenario_with_source(test_session):
    new_scenario = Scenario(scenario_name="Test Scenario")
    new_source = Source(
        source_id=1, source_name="Test Source", 
        scenario=new_scenario, number_created=100
    )
    
    test_session.add(new_source)
    test_session.commit()

    fetched_scenario = test_session.query(Scenario).filter_by(scenario_name="Test Scenario").first()
    assert fetched_scenario is not None
    assert fetched_scenario.sources[0].source_name == "Test Source"
    assert fetched_scenario.sources[0].number_created == 100

# Testet die Erstellung eines minimalen Szenarios
def test_create_minimal_scenario(test_session):
    minimal_scenario = Scenario(scenario_name="Minimal Scenario")
    minimal_source = Source(
        source_id=1, source_name="Minimal Source", 
        scenario=minimal_scenario
    )
    
    test_session.add(minimal_source)
    test_session.commit()

    fetched_scenario = test_session.query(Scenario).filter_by(scenario_name="Minimal Scenario").first()
    assert fetched_scenario is not None

# Testet die Effizienz von Masseninsertionen
def test_bulk_insertion(test_session):
    scenarios = [Scenario(scenario_name=f"Scenario {i}") for i in range(1000)]
    test_session.add_all(scenarios)
    test_session.commit()
    
    sources = [
        Source(source_id=i, source_name=f"Source {i}", scenario=scenarios[i], number_created=100) 
        for i in range(1000)
    ]
    test_session.add_all(sources)
    test_session.commit()
    
    scenario_count = test_session.query(Scenario).count()
    source_count = test_session.query(Source).count()

    assert scenario_count == 1000
    assert source_count == 1000

# Entfernt die Datenbanktabellen nach Abschluss der Tests
@pytest.fixture(scope='module', autouse=True)
def cleanup(test_engine):
    yield
    Base.metadata.drop_all(test_engine)
