import paramiko
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.orm import declarative_base, sessionmaker
from generate_ssh_key import KEY_PATH, PASSPHRASE, REMOTE_HOST, REMOTE_USER

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
    # Connect to the remote server
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    rsa_key = paramiko.RSAKey(filename=KEY_PATH, password=PASSPHRASE)  # necessary because of paramiko issue
    try:
        ssh_client.connect(REMOTE_HOST, username=REMOTE_USER, pkey=rsa_key)
    except Exception as e:
        print(f"Error with ssh_client: {e}")

    ssh_client.close()

    # Step 2: Insert data into the database
    insert_data_to_db()


if __name__ == "__main__":
    main()
