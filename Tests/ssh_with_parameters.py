import json
import os
import argparse
import sys
from pathlib import Path
from typing import Tuple, Optional
import paramiko
from tkinter import Tk
from tkinter.filedialog import askdirectory
from getpass import getpass
from paramiko import SSHClient

import stat


# Function to establish SSH connection
def create_ssh_client(server: str, port: int, user: str, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


def is_valid(path: str) -> bool:
    base_name = os.path.basename(path)
    return not base_name.startswith('.') and base_name != '__pycache__'


def ensure_remote_directory(sftp, remote_path: str):
    """Ensure the remote directory exists, creating it if necessary."""
    try:
        sftp.stat(remote_path)
    except IOError:
        print(f"Creating remote directory: {remote_path}")
        sftp.mkdir(remote_path)
        sftp.chmod(remote_path, stat.S_IRWXU)


def transfer_file(sftp, local_file_path, remote_file_path):
    """Transfer a file using SFTP."""
    try:
        sftp.put(local_file_path, remote_file_path)
        print(f"Successfully transferred {local_file_path} to {remote_file_path}")
    except Exception as e:
        print(f"Error transferring file {local_file_path}: {e}")


# Function to transfer a folder using SFTP
def transfer_folder(ssh_client: SSHClient, local_folder_path: str, remote_folder_path: str) -> None:
    remote_folder_path = os.path.expandvars(remote_folder_path)
    print(f"Expanded remote path: {remote_folder_path}")

    sftp = ssh_client.open_sftp()

    # Ensure the base remote directory exists
    ensure_remote_directory(sftp, remote_folder_path)

    for root, dirs, files in os.walk(local_folder_path):
        relative_path = os.path.relpath(root, local_folder_path)

        # Skip directories that are not 'src' or are invalid, except base directory
        if root != local_folder_path and 'src' not in relative_path.split(os.sep):
            dirs[:] = []
            files[:] = []
            continue

        # Filter out invalid directories
        dirs[:] = [d for d in dirs if is_valid(os.path.join(root, d))]

        remote_path = os.path.join(remote_folder_path, relative_path).replace('\\', '/')
        print(f"Ensuring remote directory: {remote_path}")

        ensure_remote_directory(sftp, remote_path)

        for file in files:
            if not is_valid(file):
                continue
            local_file_path = os.path.join(root, file)
            remote_file_path = os.path.join(remote_path, file).replace('\\', '/')
            print(f"Transferring {local_file_path} to {remote_file_path}")

            transfer_file(sftp, local_file_path, remote_file_path)

    sftp.close()


# Function to select a folder using a Directory Picker
def select_folder() -> str:
    root = Tk()
    root.withdraw()  # Hide the main window
    folder_path = askdirectory()  # Open the folder selection dialog
    return folder_path


# Function to read the version number from a JSON file
def read_version_from_file(file_path: str) -> Optional[str]:
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data['version']
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return None


# Function to execute a command on the remote system
def execute_command(ssh_client: paramiko.SSHClient, command: str) -> Tuple[str, str]:
    stdin, stdout, stderr = ssh_client.exec_command(command)
    return stdout.read().decode().strip(), stderr.read().decode().strip()


# Function to check Python version
def check_python_version(
        ssh_client: paramiko.SSHClient, required_version: str, env_activation_command: str
) -> bool:
    # Activate the Python environment
    activation_command = f'source {env_activation_command} && python3 --version'
    stdout, stderr = execute_command(ssh_client, activation_command)
    if stderr:
        print(f"Error checking Python version: {stderr}")
        return False
    installed_version = stdout.split()[1]
    return installed_version.startswith(required_version)


# Function to install required libraries
def install_libraries(
        ssh_client: paramiko.SSHClient, requirements_file: str, env_activation_command: str
) -> None:
    """# Activate the Python environment
    with open(requirements_file, 'r') as file:
        libraries = file.read().splitlines()
    for library in libraries:"""
    print(requirements_file)
    execute_command(ssh_client, f'source {env_activation_command} && pip3 install -r {requirements_file}')
    print("Required libraries installed.")


# Function to read configuration from a JSON file
def read_json(filename: str) -> dict:
    # Start with the directory where the script is located
    current_dir = os.path.dirname(__file__)

    while True:
        # Construct the full path to the JSON file in the current directory
        full_path = os.path.join(current_dir, filename)

        # Check if the file exists
        if os.path.isfile(full_path):
            # File found, read and return its content
            with open(full_path, 'r') as file:
                data = json.load(file)
            return data

        # Move up to the parent directory
        parent_dir = os.path.dirname(current_dir)

        # Check if the root directory has been reached or the folder name is 'DMPG'
        if parent_dir == current_dir or os.path.basename(current_dir) == 'DMPG':
            # No more directories to check or reached the 'DMPG' folder
            raise FileNotFoundError(f"File not found: {filename}")

        # Set current directory to parent directory
        current_dir = parent_dir


def get_private_config():
    try:
        private_config: dict = read_json("private_config.json")
        return private_config
    except FileNotFoundError:
        print("Private config file not found. Have you created it? It needs to contain your username")


# Main function
def main() -> None:
    print("Reading arguments from JSON")

    public_config: dict = read_json("public_config.json")

    local_version = read_version_from_file(public_config.get('paths').get('local_version_file_path'))
    if local_version is None:
        print("Local version file not found or invalid.")
        return

    private_config: dict = get_private_config()

    try:
        # Check if input can be received
        if sys.stdin.isatty():
            print("stdin is interactive, prompting for password")
            password: str = getpass(prompt=f'SSH Password for {private_config["user"]}: ')
            print("Password input received")
        else:
            print("stdin is not interactive, cannot prompt for password")
            return
    except Exception as e:
        print(f"Error with getpass: {e}")
        return

    try:
        ssh_client = create_ssh_client(public_config.get('server').get('name'),
                                       int(public_config.get('server').get('port')),
                                       private_config.get('user'), password)
        print("SSH connection established.")

        # Check Python version
        if not check_python_version(ssh_client,
                                    public_config.get('paths').get('required_python_version'),
                                    public_config.get('paths').get('env_activation_command')):
            print(f"Python {public_config.get('paths').get('required_python_version')} "
                  f"is not installed on the remote system.")
            return

        # Check if the remote folder exists
        remote_folder_path = public_config.get('paths').get('remote_folder_path')
        print(f"Remote folder path: {remote_folder_path}")
        remote_folder_path = remote_folder_path.replace('$USER', private_config["user"])
        print(f"Remote folder path: {remote_folder_path}")
        _, error = execute_command(ssh_client, f'ls {remote_folder_path}')
        folder_exists = not bool(error)

        remote_version_file_path = public_config.get('paths').get('remote_version_file_path')
        remote_version_file_path = remote_version_file_path.replace('$USER', private_config["user"])

        if folder_exists:
            remote_version, error = execute_command(ssh_client, f'cat {remote_version_file_path}')
            if error:
                print("Error reading remote version file:", error)
                remote_version = None

            if remote_version:
                remote_version = json.loads(remote_version).get('version')

            if remote_version == local_version:
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

        transfer_folder(ssh_client, local_folder_path, remote_folder_path)
        print(f"Folder successfully transferred to {remote_folder_path}.")

        """# Update the version file on the remote system
        transfer_folder(ssh_client, os.path.dirname(public_config.get('paths').get('local_version_file_path')),
                        remote_version_file_path)
        print(f"Version file successfully transferred to {remote_version_file_path}.")"""

        # Install required libraries
        requirements_file_path = public_config.get('paths').get('requirements_file_path')
        requirements_file_path = requirements_file_path.replace('$USER', private_config["user"])
        install_libraries(ssh_client,
                          requirements_file_path,
                          public_config.get('paths').get('env_activation_command'))

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        ssh_client.close()
        print("SSH connection closed.")


if __name__ == "__main__":
    main()

