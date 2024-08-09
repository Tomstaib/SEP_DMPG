import paramiko
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.orm import declarative_base, sessionmaker

# SSH/SFTP Connection Parameters
ssh_host = 'imt-sep-001.lin.hs-osnabrueck.de'
ssh_port = 22
ssh_username = 'sep'
ssh_password = 'oishooX2iefeiNai'
local_file_path = '/home/thoadelt/MachineLearning/__init__.py'
remote_file_path = './'

# Database Connection Parameters
db_user = 'sep'
db_password = 'oishooX2iefeiNai'
db_host = 'imt-sep-001.lin.hs-osnabrueck.de'
db_port = '55432'
db_name = 'sep'
db_url_template = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

# SQLAlchemy setup
Base = declarative_base()


class YourTableName(Base):
    __tablename__ = 'your_table_name'  # Replace 'your_table_name' with your actual table name
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    column1 = Column(String(50))
    column2 = Column(String(50))


def create_ssh_client(server, port, user, password):
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


def transfer_file(ssh_client, local_file, remote_file):
    with SCPClient(ssh_client.get_transport()) as scp:
        scp.put(local_file, remote_file)


def create_table_if_not_exists(engine):
    Base.metadata.create_all(engine)  # Create all tables defined in the models


def insert_data_to_db():
    db_url = db_url_template
    engine = create_engine(db_url)
    create_table_if_not_exists(engine)  # Ensure the table is created if it doesn't exist
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        new_record = YourTableName(column1='value1', column2='value2')
        session.add(new_record)
        session.commit()
        print("Data inserted successfully")
    except Exception as error:
        session.rollback()
        print(f"Error inserting data: {error}")
    finally:
        session.close()


def main():
    # Step 1: Connect via SSH and transfer the file
    ssh_client = create_ssh_client(ssh_host, ssh_port, ssh_username, ssh_password)
    transfer_file(ssh_client, local_file_path, remote_file_path)
    ssh_client.close()

    # Step 2: Insert data into the database
    insert_data_to_db()


if __name__ == "__main__":
    main()

"""
import os
import paramiko
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError

# SSH/SFTP Connection Parameters
ssh_host = 'remote_host'
ssh_port = 22
ssh_username = os.getenv('SSH_USERNAME')
ssh_password = os.getenv('SSH_PASSWORD')
local_file_path = '/home/user/data/myfile.txt'  # Local path
remote_file_path = './'  # Remote path

# Database Connection Parameters
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST', 'localhost')  # Replace with your actual database host
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'database_name')
db_url_template = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{{}}'

# SQLAlchemy setup
Base = declarative_base()

class YourTableName(Base):
    __tablename__ = 'your_table_name'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    column1 = Column(String(50))
    column2 = Column(String(50))

def create_database_if_not_exists():
    default_db_url = db_url_template.format('postgres')
    engine = create_engine(default_db_url)
    conn = engine.connect()
    conn.execute("commit")

    try:
        conn.execute(f"CREATE DATABASE {db_name}")
        print(f"Database {db_name} created successfully.")
    except ProgrammingError as e:
        if "already exists" in str(e):
            print(f"Database {db_name} already exists.")
        else:
            raise
    finally:
        conn.close()

def create_ssh_client(server, port, user, password):
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def transfer_file(ssh_client, local_file, remote_file):
    with SCPClient(ssh_client.get_transport()) as scp:
        scp.put(local_file, remote_file)

def insert_data_to_db():
    db_url = db_url_template.format(db_name)
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        new_record = YourTableName(column1='value1', column2='value2')
        session.add(new_record)
        session.commit()
        print("Data inserted successfully")
    except Exception as error:
        session.rollback()
        print(f"Error inserting data: {error}")
    finally:
        session.close()

def main():
    # Step 1: Create database if it doesn't exist
    create_database_if_not_exists()
    
    # Step 2: Connect via SSH and transfer the file
    ssh_client = create_ssh_client(ssh_host, ssh_port, ssh_username, ssh_password)
    transfer_file(ssh_client, local_file_path, remote_file_path)
    ssh_client.close()

    # Step 3: Insert data into the database
    insert_data_to_db()

if __name__ == '__main__':
    main()
"""
