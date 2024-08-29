import os
import stat
import sys
from getpass import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import orm

DB_USER = 'sep'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'distributed_computing'
DB_PASSWORD = 'sep'

def connect_to_db():
    # Create the database URL
    db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # The password will be fetched from .pgpass automatically
    engine = create_engine(db_url)

    # Test the connection
    try:
        connection = engine.connect()
        print("Connection successful")
        return connection
    except Exception as e:
        print(f"Error: {e}")
        return None


Session = sessionmaker(bind=connect_to_db())
session = Session()

orm.create_tables()

session.commit()

###### So kann gespeichert werden #####
# model = orm.Model(123,'Test')
# session.add(model)
# session.commit()

##### So können Daten abgerufen werden ####
# session = session.query(orm.Model).all()
# print(results)

session.close()
