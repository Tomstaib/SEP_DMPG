import os
import stat
import sys
from getpass import getpass
from sqlalchemy import create_engine

DB_USER = 'sep'
DB_HOST = 'imt-sep-001.lin.hs-osnabrueck.de'
DB_PORT = '55432'
DB_NAME = 'distributed_computing'


def input_password(prompt: str = "Input the password") -> str or None:
    try:
        # Check if input can be received
        if sys.stdin.isatty():
            print("stdin is interactive, prompting for password")
            remote_password: str = getpass(prompt=prompt)
            print("Password input received")
            return remote_password
        else:
            print("stdin is not interactive, cannot prompt for password")
            exit(1)
    except Exception as e:
        print(f"Error with getpass: {e}")
        return


def create_pgpass_file(template: str):
    # Determine the path for .pgpass based on the operating system
    if os.name == 'nt':  # Windows
        pgpass_path = os.path.join(os.getenv('APPDATA'), 'postgresql', 'pgpass.conf')
    else:  # Unix/Linux/Mac
        pgpass_path = os.path.join(os.path.expanduser('~'), '.pgpass')

    # Ensure the directory exists
    os.makedirs(os.path.dirname(pgpass_path), exist_ok=True)

    with open(pgpass_path, 'w') as pgpass_file:
        pgpass_file.write(template)

    # Set the file permissions to be readable and writable only by the user
    if os.name != 'nt':
        os.chmod(pgpass_path, stat.S_IRUSR | stat.S_IWUSR)

    print(f".pgpass file created at: {pgpass_path}")


def connect_to_db():
    # Create the database URL
    db_url: str = f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
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



def main():
    db_password: str = input_password(f'Password for the database: ')
    if not db_password:
        raise ValueError("Error getting the Password")

    db_url_template: str = f'{DB_HOST}:{DB_PORT}:{DB_NAME}:{DB_USER}:{db_password}'

    create_pgpass_file(db_url_template)

    connection = connect_to_db()

    if connection:
        print("Connection successful")
        connection.close()


if __name__ == '__main__':
    main()
