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
from scp import SCPClient
from flask import session
import stat
import posixpath

from ssh_setup import setup_ssh_connection, close_ssh_connection
from model_builder import load_config




# Function to transfer a folder using SFTP
def transfer_folder(ssh_client: SSHClient, local_folder_path: str, remote_folder_path: str) -> None:
    def is_valid(path: str) -> bool:
        base_name = os.path.basename(path)
        return not base_name.startswith('.') and base_name != '__pycache__'

    def transfer_file(sftp, local_file_path, remote_file_path):
        """Transfer a file using SFTP."""
        try:
            sftp.put(local_file_path, remote_file_path)
            print(f"Successfully transferred {local_file_path} to {remote_file_path}")
        except Exception as e:
            print(f"Error transferring file {local_file_path}: {e}")

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


def ensure_remote_directory(sftp, remote_path: str):
    """Ensure the remote directory exists, creating it if necessary."""
    try:
        sftp.stat(remote_path)
    except IOError:
        print(f"Creating remote directory: {remote_path}")
        sftp.mkdir(remote_path)
        sftp.chmod(remote_path, stat.S_IRWXU)


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
    print(ssh_client)
    stdin, stdout, stderr = ssh_client.exec_command(command)
    return stdout.read().decode().strip(), stderr.read().decode().strip()


# Function to check Python version
"""def check_python_version(
        ssh_client: paramiko.SSHClient, required_version: str, env_activation_command: str
) -> bool:
    # Activate the Python environment
    activation_command = f'source {env_activation_command} && python3 --version'
    stdout, stderr = execute_command(ssh_client, activation_command)
    if stderr:
        print(f"Error checking Python version: {stderr}")
        return False
    installed_version = stdout.split()[1]
    return installed_version.startswith(required_version)"""


def check_venv_exists(ssh_client: paramiko.SSHClient, venv_path: str,
                      env_activation_command: str, required_version: str) -> bool:
    # Check if venv directory exists
    stdout, stderr = execute_command(ssh_client, f'if [ -f {env_activation_command} ]; then echo "exists"; fi')

    if "exists" not in stdout:
        print(f"Virtual environment at {venv_path} does not exist. Creating it...")
        create_venv(ssh_client, venv_path)

    # Check the Python version inside the virtual environment
    activation_command = f'source {env_activation_command} && python3 --version'
    stdout, stderr = execute_command(ssh_client, activation_command)

    if stderr:
        print(f"Error checking Python version: {stderr}")
        return False

    installed_version = stdout.split()[1]
    if not installed_version.startswith(required_version):
        print(
            f"Installed Python version ({installed_version}) does not match the required version ({required_version}).")
        return False

    return True


def create_venv(ssh_client: paramiko.SSHClient, venv_path: str) -> None:
    command = f'mkdir /cluster/user/$USER/venvs'
    execute_command(ssh_client, command)

    # Create virtual environment
    command = f'python3 -m venv {venv_path}'
    stdout, stderr = execute_command(ssh_client, command)
    if stderr:
        print(f"Error creating virtual environment: {stderr}")
        exit(1)
    else:
        print(f"Virtual environment created at {venv_path}")


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
def prepare_env(username) -> None:

    print("Reading arguments from JSON")

    public_config: dict = read_json("public_config.json")
    print(public_config.get('paths').get('local_version_file_path'))
    local_version = read_version_from_file(public_config.get('paths').get('local_version_file_path'))
    if local_version is None:
        print("Local version file not found or invalid.")
        return

    try:
        ssh_client = setup_ssh_connection(username)
        print(ssh_client)
        print("SSH connection established.")

        # Check Python version
        """if not check_python_version(ssh_client,
                                    public_config.get('paths').get('required_python_version'),
                                    public_config.get('paths').get('env_activation_command')):
            print(f"Python {public_config.get('paths').get('required_python_version')} "
                  f"is not installed on the remote system.")
            return"""
        # Check if the virtual environment exists and has the correct Python version
        """if not check_venv_exists(ssh_client,
                                 public_config.get('paths').get('venv_path'),
                                 public_config.get('paths').get('env_activation_command'),
                                 public_config.get('paths').get('required_python_version')):
            print(f"Python virtual environment or required version "
                  f"{public_config.get('paths').get('required_python_version')} is not installed.")
            return"""

        # Check if the remote folder exists
        remote_folder_path = public_config.get('paths').get('remote_folder_path')
        print(f"Remote folder path: {remote_folder_path}")
        remote_folder_path = remote_folder_path.replace('$USER', username)
        print(f"Remote folder path: {remote_folder_path}")
        _, error = execute_command(ssh_client, f'ls {remote_folder_path}')
        folder_exists = not bool(error)

        remote_version_file_path = public_config.get('paths').get('remote_version_file_path')
        remote_version_file_path = remote_version_file_path.replace('$USER', username)

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
                requirements_file_path = requirements_file_path.replace('$USER', username)
                install_libraries(ssh_client,
                                  requirements_file_path,
                                  public_config.get('paths').get('env_activation_command'))
                return

        print("The software needs to be updated.")
        local_folder_path = public_config.get('paths').get('local_folder_path')

        transfer_folder(ssh_client, local_folder_path, remote_folder_path)
        print(f"Folder successfully transferred to {remote_folder_path}.")
        if not check_venv_exists(ssh_client,
                                 public_config.get('paths').get('venv_path'),
                                 public_config.get('paths').get('env_activation_command'),
                                 public_config.get('paths').get('required_python_version')):
            print(f"Python virtual environment or required version "
                  f"{public_config.get('paths').get('required_python_version')} is not installed.")
            return
        # Install required libraries
        requirements_file_path = public_config.get('paths').get('requirements_file_path')
        requirements_file_path = requirements_file_path.replace('$USER',username)
        install_libraries(ssh_client,
                          requirements_file_path,
                          public_config.get('paths').get('env_activation_command'))

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        close_ssh_connection(ssh_client)
        print("SSH connection closed.")


def transfer_experiments(ssh_client: paramiko.SSHClient, local_model_path: str, username: str) -> None:
    try:
        sftp = ssh_client.open_sftp()
    except Exception as e:
        print(f"Error opening SFTP session: {str(e)}")
        return

    remote_folder: str = f'/cluster/user/{username}/DMPG_experiments'

    try:
        # Ensure the root folder exists
        ensure_remote_directory(sftp, remote_folder)

        # Recursively upload files and directories
        upload_directory(sftp, local_model_path, remote_folder)

    except Exception as e:
        print(f"Error during transfer: {str(e)}")
    finally:
        sftp.close()


def upload_directory(sftp, local_dir: str, remote_dir: str) -> None:
    """
    Recursively upload a directory and its contents to the remote directory.

    :param sftp: The active SFTP session
    :param local_dir: The local directory to upload
    :param remote_dir: The remote directory to upload to
    """
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = posixpath.join(remote_dir, item)

        if os.path.isfile(local_path):
            # Upload the file
            try:
                print(f"Uploading file {local_path} to {remote_path}")
                if local_path.endswith('.json'):
                    manipulate_arrival_table_path(local_path, remote_path)
                sftp.put(local_path, remote_path)
            except Exception as e:
                print(f"Failed to upload {local_path}: {str(e)}")

        elif os.path.isdir(local_path):
            # Ensure remote directory exists
            ensure_remote_directory(sftp, remote_path)
            # Recursively upload the contents of the directory
            upload_directory(sftp, local_path, remote_path)


def manipulate_arrival_table_path(json_path: str, remote_path: str) -> None:
    config_data = load_config(json_path)

    for source in config_data.get('sources', []):
        arrival_table = source.get('arrival_table', "")
        if arrival_table:
            # Split the path from 'arrival_tables' onwards
            relative_path = arrival_table.split('arrival_tables', 1)[-1].lstrip("\\/")

            remote_path_without_json = posixpath.dirname(remote_path)

            # Join the relative path to the remote base path
            new_remote_path = posixpath.join(remote_path_without_json, 'arrival_tables', relative_path)

            source['arrival_table'] = new_remote_path

    with open(json_path, 'w') as file:
        json.dump(config_data, file, indent=4)

def manipulate_scenario_path(original_path):
    """
    Wandelt den Pfad von /var/www/dmpg_api/user/{user}/{Modell}/{Szenario}/{filename}
    in den Pfad /cluster/user/{user}/DMPG_experiments/{Modell}/{Szenario}/arrival_tables/{filename} um.
    """
    # Zerlege den originalen Pfad
    parts = original_path.split(os.sep)
    
    # Sicherstellen, dass der Pfad die erwartete Struktur hat
    if len(parts) < 7 or parts[0] != '' and parts[1] != 'var' and parts[2] != 'www' and parts[3] != 'dmpg_api' and parts[4] != 'user':
        raise ValueError("Invalid path structure")
    
    # Extrahiere die relevanten Teile des Pfads
    user = parts[5]          # Benutzername (z.B. 'thoadelt')
    model = parts[6]         # Modell (z.B. 'a')
    scenario = parts[7]      # Szenario (z.B. 'ss')
    filename = parts[-1]     # Dateiname (z.B. 'a_ss.json')
    
    # Setze den neuen Pfad zusammen
    new_path = os.path.join("/cluster", "user", user, "DMPG_experiments", model, scenario, filename)
    
    return new_path


def send_db_key(ssh_client: SSHClient, username: str):
    try:
        sftp = ssh_client.open_sftp()
    except Exception as e:
        print("Error opening sftp", e)
    stdin, stdout, stderr = ssh_client.exec_command('whoami')
    sftp_user = stdout.read().decode().strip()
    print(f"You are logged in as: {sftp_user}")
    try:
        local_path = os.path.join("/var/www/dmpg_api", "generate_db_key.py")
        print("Local path:", local_path)
        remote_path = f"/home/{username}/generate_db_key.py"
        sftp.put(local_path, remote_path)
    except Exception as e:
        print("Error putting to slurm", e)
        exit(1)

    try:
        stdin, stdout, stderr = ssh_client.exec_command(f"pip install --user sqlalchemy")
        # Activate the virtual environment
        stdin, stdout, stderr = ssh_client.exec_command(f"source /cluster/user/{username}/venvs/DMPG/bin/activate")
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        print("Activated virtual environment")
        error_message = stderr.read().decode()
        if error_message:
            print(f"Error activating virtual environment: {error_message}")

        # Run the Python script
        stdin, stdout, stderr = ssh_client.exec_command(f"python3 {remote_path}")
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        print("Started script")
        error_message = stderr.read().decode()
        if error_message:
            print(f"Error running script: {error_message}")
        
        # Deactivate the virtual environment
        stdin, stdout, stderr = ssh_client.exec_command("deactivate")
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        print("Deactivated virtual environment")
        error_message = stderr.read().decode()
        if error_message:
            print(f"Error deactivating virtual environment: {error_message}")
        
        # Remove the script from the remote server
        stdin, stdout, stderr = ssh_client.exec_command(f"rm {remote_path}")
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        print("Removed the script")
        error_message = stderr.read().decode()
        if error_message:
            print(f"Error removing script: {error_message}")
    
    except Exception as e:
        print(f"An error occurred during remote command execution: {e}")
