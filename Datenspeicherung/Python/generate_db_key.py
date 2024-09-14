import os
import stat
import sys
from getpass import getpass
from sqlalchemy import create_engine
import psycopg2
from sqlalchemy.exc import OperationalError

DB_USER = 'sep'
DB_HOST = 'imt-sep-001.lin.hs-osnabrueck.de'
DB_PORT = '55432'
DB_NAME = 'distributed_computing'

def input_password() -> str or None:
    try:
        if sys.stdin.isatty():
            print("stdin is interactive, prompting for password")
            remote_password: str = getpass(prompt=f'Password for the database: ')
            print("Password input received")
            return remote_password
        else:
            print("stdin is not interactive, cannot prompt for password")
            exit(1)
    except Exception as e:
        print(f"Error with getpass: {e}")
        sys.exit(1)

def create_pgpass_file(template):
    downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
    pgpass_path = os.path.join(downloads_dir, 'pgpass.conf')

    # Überprüfe, ob das Verzeichnis existiert, bevor es erstellt wird
    try:
        os.makedirs(os.path.dirname(pgpass_path), exist_ok=True)
    except PermissionError as e:
        print(f"Error writing .pgpass file: {e}")
        return  # Fehlerhaft, keine weiteren Schritte unternehmen

    try:
        with open(pgpass_path, 'w') as f:
            f.write(template)
        print(f"Saving .pgpass file to: {pgpass_path}")
    except Exception as e:
        print(f"Error writing .pgpass file: {e}")

    if os.name != 'nt':
        try:
            os.chmod(pgpass_path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception as e:
            print(f"Error setting permissions: {e}")



def connect_to_db():
    # Create the database URL
    db_url = f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print(f"Connecting to database with URL: {db_url}")  # Debug-Ausgabe
    # The password will be fetched from .pgpass automatically
    engine = create_engine(db_url)
    print(f"Engine object: {engine}")  # Debug-Ausgabe

    # Test the connection
    try:
        connection = engine.connect()
        print(f"Connection object: {connection}")  # Debug-Ausgabe
        print("Connection successful")
        return connection
    except Exception as e:
        print(f"Error: {e}")
        return None




def main():
    db_password: str = input_password()
    if not db_password:
        raise ValueError("Error getting the Password")

    db_url_template: str = f'{DB_HOST}:{DB_PORT}:{DB_NAME}:{DB_USER}:{db_password}'

    create_pgpass_file(db_url_template)

    connection = connect_to_db()

    if connection:
        print("Connection successful")
        connection.close()
    else:
        print("Connection unsuccessful")

if __name__ == '__main__': # pragma: no cover
    main()
