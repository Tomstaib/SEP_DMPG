import json
import os
import sys
from typing import Tuple, Optional
import paramiko
from tkinter import Tk
from tkinter.filedialog import askdirectory
from getpass import getpass
import stat


def create_ssh_client(server: str, port: int, user: str, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


def is_valid(path: str) -> bool:
    base_name = os.path.basename(path)
    return not base_name.startswith('.') and base_name != '__pycache__'


def ensure_remote_directory(sftp: paramiko.SFTPClient, remote_path: str):
    remote_path = remote_path.replace('\\', '/')  # Normalisierung
    try:
        sftp.stat(remote_path)
    except IOError:
        print(f"Creating remote directory: {remote_path}")
        sftp.mkdir(remote_path)
        print(f"Setting permissions for directory: {remote_path}")
        sftp.chmod(remote_path, stat.S_IRWXU)  # Setze Berechtigungen
    except Exception as e:
        print(f"Error ensuring remote directory {remote_path}: {e}")
        raise




def transfer_file(sftp, local_file_path, remote_file_path):
    local_file_path = local_file_path.replace('\\', '/')
    remote_file_path = remote_file_path.replace('\\', '/')  # Normalisierung
    try:
        sftp.put(local_file_path, remote_file_path)
        print(f"Successfully transferred {local_file_path} to {remote_file_path}")
    except Exception as e:
        print(f"Error transferring file {local_file_path}: {e}")
        raise


def transfer_folder(ssh_client: paramiko.SSHClient, local_folder_path: str, remote_folder_path: str):
    sftp = ssh_client.open_sftp()
    remote_folder_path = os.path.expanduser(remote_folder_path).replace('\\', '/')
    print(f"Expanded remote path: {remote_folder_path}")

    # Debug-Ausgabe hinzufügen
    print(f"Calling ensure_remote_directory for: {remote_folder_path}")
    ensure_remote_directory(sftp, remote_folder_path)

    for root, dirs, files in os.walk(local_folder_path):
        relative_path = os.path.relpath(root, local_folder_path).replace('\\', '/')
        dirs[:] = [d for d in dirs if is_valid(os.path.join(root, d))]

        remote_path = os.path.normpath(os.path.join(remote_folder_path, relative_path)).replace('\\', '/')
        print(f"Ensuring remote directory: {remote_path}")

        # Debug-Ausgabe hinzufügen
        print(f"Calling ensure_remote_directory for: {remote_path}")
        ensure_remote_directory(sftp, remote_path)

        for file in files:
            if not is_valid(file):
                continue
            local_file_path = os.path.join(root, file)
            remote_file_path = os.path.normpath(os.path.join(remote_path, file)).replace('\\', '/')
            print(f"Transferring {local_file_path} to {remote_file_path}")

            transfer_file(sftp, local_file_path, remote_file_path)

    sftp.close()




def select_folder() -> str:
    root = Tk()
    root.withdraw()
    folder_path = askdirectory()
    return folder_path


def read_version_from_file(file_path: str) -> Optional[str]:
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data['version']
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except KeyError:
        print(f"Version key not found in the file: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error in file {file_path}: {e}")
        return None


def execute_command(ssh_client: paramiko.SSHClient, command: str) -> Tuple[str, str]:
    stdin, stdout, stderr = ssh_client.exec_command(command)
    return stdout.read().decode().strip(), stderr.read().decode().strip()


def check_python_version(
        ssh_client: paramiko.SSHClient, required_version: str, env_activation_command: str
) -> bool:
    activation_command = f'{env_activation_command} && python3 --version'
    stdout, stderr = execute_command(ssh_client, activation_command)

    if stderr:
        print(f"Error checking Python version: {stderr}")
        return False

    installed_version = stdout.split()[1]
    return installed_version.startswith(required_version)


def install_libraries(
        ssh_client: paramiko.SSHClient, requirements_file: str, env_activation_command: str
) -> None:
    print(requirements_file)

    execute_command(ssh_client, f'{env_activation_command} && pip3 install -r {requirements_file}')
    print("Required libraries installed.")



def read_json(filename: str) -> dict:
    current_dir = os.path.dirname(os.path.abspath(__file__))

    while True:
        full_path = os.path.join(current_dir, filename)

        if os.path.isfile(full_path):
            with open(full_path, 'r') as file:
                data = json.load(file)
            return data

        parent_dir = os.path.dirname(current_dir)

        if parent_dir == current_dir or os.path.basename(current_dir) == 'DMPG':
            raise FileNotFoundError(f"File not found: {filename}")

        current_dir = parent_dir


def get_private_config():
    try:
        private_config = read_json("private_config.json")
        return private_config
    except FileNotFoundError:
        print("Private config file not found. Have you created it? It needs to contain your username")
        return None


def main() -> None:
    print("Reading arguments from JSON")

    try:
        public_config: dict = read_json("public_config.json")
        print("Public config loaded")
    except FileNotFoundError:
        print("public_config.json file not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding public_config.json: {e}")
        return

    local_version = read_version_from_file(public_config.get('paths').get('local_version_file_path'))
    if local_version is None:
        print("Local version file not found or invalid.")
        return
    print(f"Local version: {local_version}")

    private_config: dict = get_private_config()
    if private_config is None:
        print("Private config is None.")
        return

    ssh_client = None  # Initialisierung von ssh_client

    try:
        print("stdin is interactive, prompting for password")
        # Ersetzen von getpass durch input
        password: str = input(f'SSH Password for {private_config["user"]}: ')
        print("Password input received")

        print("Attempting to create SSH client...")
        ssh_client = create_ssh_client(public_config.get('server').get('name'),
                                       int(public_config.get('server').get('port')),
                                       private_config.get('user'), password)
        print("SSH connection established.")

        print("Checking Python version on remote system...")
        if not check_python_version(ssh_client,
                                    public_config.get('paths').get('required_python_version'),
                                    public_config.get('paths').get('env_activation_command')):
            print(f"Python {public_config.get('paths').get('required_python_version')} "
                  f"is not installed on the remote system.")
            return

        remote_folder_path = public_config.get('paths').get('remote_folder_path')
        remote_folder_path = remote_folder_path.replace('$USER', private_config["user"])
        _, error = execute_command(ssh_client, f'ls {remote_folder_path}')
        folder_exists = not bool(error)
        print(f"Remote folder exists: {folder_exists}")

        remote_version_file_path = public_config.get('paths').get('remote_version_file_path')
        remote_version_file_path = remote_version_file_path.replace('$USER', private_config["user"])

        if folder_exists:
            remote_version, error = execute_command(ssh_client, f'cat {remote_version_file_path}')
            if error:
                print(f"Error reading remote version file: {error}")
                remote_version = None

            print(f"Remote version: {remote_version}")

            if remote_version and remote_version == local_version:
                print("The software is already up to date. No transfer needed.")
                requirements_file_path = public_config.get('paths').get('requirements_file_path')
                requirements_file_path = requirements_file_path.replace('$USER', private_config["user"])
                install_libraries(ssh_client,
                                  requirements_file_path,
                                  public_config.get('paths').get('env_activation_command'))
                return

        print("The software needs to be updated.")
        local_folder_path = select_folder()
        if not local_folder_path:
            print("No folder selected.")
            return

        print(f"Transferring folder from {local_folder_path} to {remote_folder_path}")
        transfer_folder(ssh_client, local_folder_path, remote_folder_path)

        print(f"Folder successfully transferred to {remote_folder_path}.")

        transfer_folder(ssh_client, os.path.dirname(public_config.get('paths').get('local_version_file_path')),
                        remote_version_file_path)
        print(f"Version file successfully transferred to {remote_version_file_path}.")

        requirements_file_path = public_config.get('paths').get('requirements_file_path')
        requirements_file_path = requirements_file_path.replace('$USER', private_config["user"])
        install_libraries(ssh_client,
                          requirements_file_path,
                          public_config.get('paths').get('env_activation_command'))

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if ssh_client:  # Überprüfung, ob ssh_client nicht None ist
            ssh_client.close()
            print("SSH connection closed.")





if __name__ == "__main__":
    main() # pragma: no cover
