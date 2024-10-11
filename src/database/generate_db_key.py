import os
import stat
import sys
from getpass import getpass
from typing import Optional
from database_params import DB_USER, DB_HOST, DB_PORT, DB_NAME, DB_PASSWORD  # direct import necessary because of generate_db_key


DB_URL_TEMPLATE: str = f'{DB_HOST}:{DB_PORT}:{DB_NAME}:{DB_USER}:{DB_PASSWORD}'
"""Constant for the expected format in the .pgpass file."""


def input_password(prompt: str = "Input the password") -> Optional[str]:
    """
    Input the password. This is only possible if the console input is possible.

    :param prompt: The password prompt.

    :return: The password provided by the user or None if input is not possible.
    """
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


def create_pgpass_file(template: str = DB_URL_TEMPLATE):
    """
    Create the .pgpass file needed for passwordless connection to the postgresql database.

    :param template: The template for the .pgpass file provided as a constant.
    """
    # Determine the path for .pgpass based on the operating system
    if os.name == 'nt':  # Windows
        pgpass_path: str = os.path.join(os.getenv('APPDATA'), 'postgresql', 'pgpass.conf')
    else:  # Unix/Linux/Mac
        pgpass_path: str = os.path.join(os.path.expanduser('~'), '.pgpass')

    # Ensure the directory exists
    os.makedirs(os.path.dirname(pgpass_path), exist_ok=True)

    with open(pgpass_path, 'w') as pgpass_file:
        pgpass_file.write(template)

    # Set the file permissions to be readable and writable only by the user
    if os.name != 'nt':
        os.chmod(pgpass_path, stat.S_IRUSR | stat.S_IWUSR)

    print(f".pgpass file created at: {pgpass_path}")


def main():
    if not DB_PASSWORD:
        raise ValueError("Error getting the Password")

    create_pgpass_file(DB_URL_TEMPLATE)


if __name__ == '__main__':
    main()
