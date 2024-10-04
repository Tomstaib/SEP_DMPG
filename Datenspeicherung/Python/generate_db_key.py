import os
import stat
import sys
from getpass import getpass
from database_params import DB_USER, DB_HOST, DB_PORT, DB_NAME, DB_PASSWORD
from database_connection import connect_to_db


DB_URL_TEMPLATE: str = f'{DB_HOST}:{DB_PORT}:{DB_NAME}:{DB_USER}:{DB_PASSWORD}'


def input_password(prompt: str = "Input the password") -> str | None:
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
    # Bestimme den Pfad für die .pgpass-Datei basierend auf dem Betriebssystem
    if os.name == 'nt':  # Windows
        appdata_path = os.getenv('APPDATA')
        if not appdata_path:
            raise ValueError("Die APPDATA-Umgebungsvariable ist nicht gesetzt oder leer")
        pgpass_path: str = os.path.join(appdata_path, 'postgresql', 'pgpass.conf')
    else:  # Unix/Linux/Mac
        home_dir = os.path.expanduser('~')
        if not home_dir:
            raise ValueError("Das Home-Verzeichnis konnte nicht ermittelt werden")
        pgpass_path: str = os.path.join(home_dir, '.pgpass')

    # Stelle sicher, dass das Verzeichnis existiert
    os.makedirs(os.path.dirname(pgpass_path), exist_ok=True)

    # Schreibe das Template in die .pgpass-Datei
    try:
        with open(pgpass_path, 'w') as pgpass_file:
            pgpass_file.write(template)
    except OSError as e:
        raise OSError(f"Fehler beim Schreiben der .pgpass-Datei: {e}")

    # Setze die Dateiberechtigungen so, dass sie nur vom Benutzer gelesen und geschrieben werden können
    if os.name != 'nt':
        try:
            os.chmod(pgpass_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError as e:
            raise OSError(f"Fehler beim Setzen der Dateiberechtigungen: {e}")

    print(f".pgpass-Datei erstellt unter: {pgpass_path}")


def main():
    if not DB_PASSWORD:
        raise ValueError("Error getting the Password")

    create_pgpass_file(DB_URL_TEMPLATE)

    connection = connect_to_db()

    if connection:
        print("Connection successful")
        connection.close()




if __name__ == '__main__':
    main() #pragma: no cover
