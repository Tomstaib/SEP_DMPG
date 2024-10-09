import json
import os
from typing import Optional
import paramiko
from paramiko import SSHClient
import stat
import posixpath
from paramiko.sftp_client import SFTPClient
from src.util.flask.ssh_setup import setup_ssh_connection, close_ssh_connection
from src.util.helper import load_config


def transfer_dmpg_folder(ssh_client: SSHClient, local_folder_path: str, remote_folder_path: str) -> None:
    """
    Transfer the DMPG folder to the remote.

    :param ssh_client: SSHClient connected to the remote.
    :param local_folder_path: Local DMPG folder path.
    :param remote_folder_path: Remote DMPG folder path.
    """

    def is_valid(path: str) -> bool:
        """
        Checks if the directory is pycache or starts with a dot. Dotfiles, dotdirectories and pycache should be ignored.

        :param path: Path to check.
        """
        base_name = os.path.basename(path)
        return (not base_name.startswith('.') and base_name != '__pycache__'
                and base_name != 'user' and base_name != 'static' and base_name != 'templates')

    def transfer_file(sftp: SFTPClient, local_file_path: str, remote_file_path: str):
        """Transfer a file using SFTP."""
        try:
            sftp.put(local_file_path, remote_file_path)
            print(f"Successfully transferred {local_file_path} to {remote_file_path}")
        except Exception as e:
            print(f"Error transferring file {local_file_path}: {e}")

    remote_folder_path: str = os.path.expandvars(remote_folder_path)

    sftp: SFTPClient = ssh_client.open_sftp()

    ensure_remote_directory(sftp, remote_folder_path)

    for root, dirs, files in os.walk(local_folder_path):
        relative_path: str = os.path.relpath(root, local_folder_path)

        # Skip directories that are not 'src' or are invalid, except base directory
        if root != local_folder_path and 'src' not in relative_path.split(os.sep):
            dirs[:] = []
            files[:] = []
            continue

        # Filter out invalid directories
        dirs[:] = [d for d in dirs if is_valid(os.path.join(root, d))]

        remote_path: str = os.path.join(remote_folder_path, relative_path).replace('\\', '/')
        print(f"Ensuring remote directory: {remote_path}")

        ensure_remote_directory(sftp, remote_path)

        for file in files:
            if not is_valid(file):
                continue
            local_file_path: str = os.path.join(root, file)
            remote_file_path: str = os.path.join(remote_path, file).replace('\\', '/')
            print(f"Transferring {local_file_path} to {remote_file_path}")

            transfer_file(sftp, local_file_path, remote_file_path)

    sftp.close()


def ensure_remote_directory(sftp: SFTPClient, remote_path: str):
    """
    Ensure the remote directory exists, creating it if necessary.

    :param sftp: SFTPClient connected to the remote.
    :param remote_path: Remote directory path.
    """
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


def execute_command(ssh_client: paramiko.SSHClient, command: str) -> (str, str):
    """
    Execute a command on the remote host and return the output of the command.

    :param ssh_client: SSHClient connected to the remote.
    :param command: Command to execute.
    """
    _, stdout, stderr = ssh_client.exec_command(command)
    return stdout.read().decode().strip(), stderr.read().decode().strip()


def check_venv_exists(ssh_client: paramiko.SSHClient, venv_path: str,
                      env_activation_command: str, required_version: str) -> bool:
    """
    Check if the virtual environment exists on the remote.

    :param ssh_client: SSHClient connected to the remote.
    :param venv_path: Path to the virtual environment.
    :param env_activation_command: Command to activate the virtual environment.
    :param required_version: Required version of python.

    :return: True if the virtual environment exists and matches the required version on the remote, False otherwise.
    """
    stdout, stderr = execute_command(ssh_client, f'if [ -f {env_activation_command} ]; then echo "exists"; fi')

    if "exists" not in stdout:
        print(f"Virtual environment at {venv_path} does not exist. Creating it...")
        create_venv(ssh_client, venv_path)

    # Check the Python version inside the virtual environment
    activation_command: str = f'source {env_activation_command} && python3 --version'
    stdout, stderr = execute_command(ssh_client, activation_command)

    if stderr:
        print(f"Error checking Python version: {stderr}")
        return False

    installed_version: str = stdout.split()[1]
    if not installed_version.startswith(required_version):
        print(
            f"Installed Python version ({installed_version}) does not match the required version ({required_version}).")
        return False

    return True


def create_venv(ssh_client: paramiko.SSHClient, venv_path: str) -> None:
    """
    Create a virtual environment on the remote.

    :param ssh_client: SSHClient connected to the remote.
    :param venv_path: Path to the virtual environment.
    """
    command: str = 'mkdir /cluster/user/$USER/venvs'
    execute_command(ssh_client, command)

    # Create virtual environment
    command = f'python3 -m venv {venv_path}'
    _, stderr = execute_command(ssh_client, command)
    if stderr:
        print(f"Error creating virtual environment: {stderr}")
        exit(1)
    else:
        print(f"Virtual environment created at {venv_path}")


def install_libraries(ssh_client: paramiko.SSHClient, requirements_file: str, env_activation_command: str) -> None:
    print(requirements_file)
    execute_command(ssh_client, f'source {env_activation_command} && pip3 install -r {requirements_file}')
    print("Required libraries installed.")


def read_json(filename: str) -> dict:
    """
    Helper function to read config.json
    """
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


def prepare_env(username: str) -> None:
    """
    Function to prepare the environment on the remote. Meaning correct python with venv and DMPG on the remote.
    The replacement is because the environment variable user couldn't be expanded.

    :param username: Username of the user who wants to prepare the environment.
    """

    public_config: dict = read_json("public_config.json")
    print(public_config.get('paths').get('local_version_file_path'))
    local_version: str = read_version_from_file(public_config.get('paths').get('local_version_file_path'))
    if local_version is None:
        print("Local version file not found or invalid.")
        return

    remote_user: str = '$USER'

    try:
        ssh_client: SSHClient = setup_ssh_connection(username)
        print("SSH connection established.")

        # Check if the remote folder exists
        remote_folder_path: str = public_config.get('paths').get('remote_folder_path')
        print(f"Remote folder path: {remote_folder_path}")
        remote_folder_path: str = remote_folder_path.replace(remote_user, username)
        print(f"Remote folder path: {remote_folder_path}")
        _, error = execute_command(ssh_client, f'ls {remote_folder_path}')
        folder_exists = not bool(error)

        remote_version_file_path: str = public_config.get('paths').get('remote_version_file_path')
        remote_version_file_path: str = remote_version_file_path.replace(remote_user, username)

        if folder_exists:
            remote_version, error = execute_command(ssh_client, f'cat {remote_version_file_path}')
            if error:
                print("Error reading remote version file:", error)
                remote_version: Optional[str] = None

            if remote_version:
                remote_version: str = json.loads(remote_version).get('version')

            if remote_version == local_version:
                print("The software is already up to date. No transfer needed.")
                requirements_file_path: str = public_config.get('paths').get('requirements_file_path')
                requirements_file_path: str = requirements_file_path.replace(remote_user, username)
                install_libraries(ssh_client,
                                  requirements_file_path,
                                  public_config.get('paths').get('env_activation_command'))
                return

        print("The software needs to be updated.")
        local_folder_path: str = public_config.get('paths').get('local_folder_path')

        transfer_dmpg_folder(ssh_client, local_folder_path, remote_folder_path)
        print(f"Folder successfully transferred to {remote_folder_path}.")
        if not check_venv_exists(ssh_client,
                                 public_config.get('paths').get('venv_path'),
                                 public_config.get('paths').get('env_activation_command'),
                                 public_config.get('paths').get('required_python_version')):
            print(f"Python virtual environment or required version "
                  f"{public_config.get('paths').get('required_python_version')} is not installed.")
            return

        # Install required libraries
        requirements_file_path: str = public_config.get('paths').get('requirements_file_path')
        requirements_file_path: str = requirements_file_path.replace(remote_user, username)
        install_libraries(ssh_client,
                          requirements_file_path,
                          public_config.get('paths').get('env_activation_command'))

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        close_ssh_connection(ssh_client)
        print("SSH connection closed.")


def transfer_experiments(ssh_client: paramiko.SSHClient, local_model_path: str, username: str) -> None:
    """
    Upload the configuration files of the simulation to the remote.
    """
    try:
        sftp: SFTPClient = ssh_client.open_sftp()
    except Exception as e:
        print(f"Error opening SFTP session: {str(e)}")
        return

    remote_folder: str = f'/cluster/user/{username}/DMPG_experiments'

    try:
        # Ensure the root folder exists
        ensure_remote_directory(sftp, remote_folder)

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
        local_path: str = os.path.join(local_dir, item)
        remote_path: str = posixpath.join(remote_dir, item)

        if os.path.isfile(local_path):
            try:
                print(f"Uploading file {local_path} to {remote_path}")
                if local_path.endswith('.json'):
                    manipulate_arrival_table_path(local_path, remote_path)
                sftp.put(local_path, remote_path)
            except Exception as e:
                print(f"Failed to upload {local_path}: {str(e)}")

        elif os.path.isdir(local_path):

            ensure_remote_directory(sftp, remote_path)
            # Recursive call to upload directory
            upload_directory(sftp, local_path, remote_path)


def manipulate_arrival_table_path(json_path: str, remote_path: str) -> None:
    """
    Manipulate the arrival table path of the sources arrival tables to fit the clusters directory. Use posix to ensure
    no problems with (back-)slashes based on different os.

    :param json_path: The json file path to the simulation configuration.
    :param remote_path: The remote path to change the arrival tables path to.
    """
    config_data: dict = load_config(json_path)

    for source in config_data.get('sources', []):
        arrival_table: str = source.get('arrival_table', "")
        if arrival_table:
            # Split the path from 'arrival_tables' onwards
            relative_path: str = arrival_table.split('arrival_tables', 1)[-1].lstrip("\\/")

            remote_path_without_json: str = posixpath.dirname(remote_path)

            # Join the relative path to the remote base path
            new_remote_path = posixpath.join(remote_path_without_json, 'arrival_tables', relative_path)

            source['arrival_table'] = new_remote_path

    with open(json_path, 'w') as file:
        json.dump(config_data, file, indent=4)


def manipulate_scenario_path(original_path: str, source_base_path: str,
                             destination_base_path_template: str) -> str:
    """
    Changes path from {app.root_path}/user/{user}/{model}/{scenario}/{filename}
    to /cluster/user/$USER/DMPG_experiments/{model}/{scenario}/arrival_tables/{filename}.
    """
    # Extract relative path from source base path
    try:
        relative_path: str = os.path.relpath(original_path, source_base_path)
    except ValueError as e:
        raise ValueError(f"Invalid path structure: {e}")
    print(relative_path)

    # Split relative path
    parts: list[str] = original_path.split(os.sep)

    if len(parts) < 3:
        raise ValueError("Invalid path structure: Expected at least 3 parts in the relative path")

    user, model, scenario = parts[-4], parts[-3], parts[-2]
    filename = parts[-1]

    # Construct the destination base path using the template
    destination_base_path: str = destination_base_path_template.format(user=user)

    # Construct the new path
    new_path: str = posixpath.join(destination_base_path, model, scenario, filename)
    print(new_path)

    return new_path


def create_db_key_on_remote(ssh_client: SSHClient, local_path: str, remote_path: str) -> None:
    """
    Create the .pgpass on the remote.

    :param ssh_client: The active SSH session.
    :param local_path: The local file to upload.
    :param remote_path: The remote file to upload to.

    See also:
        -[send_file_to_remote](../util/flask/environment.html#send_file_to_remote): Sends a file to the remote.
        -[run_remote_python_script](../util/flask/environment.html#run_remote_python_script): Runs a python script on the remote.
        -[remove_remote_file](../util/flask/environment.html#remove_remote_file): Removes a file on the remote.
    """
    try:
        generate_db_key_file: str = "generate_db_key.py"
        send_file_to_remote(ssh_client, os.path.join(local_path, generate_db_key_file),
                            posixpath.join(remote_path, generate_db_key_file))
        db_params_file: str = "database_params.py"
        send_file_to_remote(ssh_client, os.path.join(local_path, db_params_file),
                            posixpath.join(remote_path, db_params_file))

        run_remote_python_script(ssh_client, posixpath.join(remote_path, generate_db_key_file), )

        remove_remote_file(ssh_client, posixpath.join(remote_path, generate_db_key_file))
        remove_remote_file(ssh_client, posixpath.join(remote_path, db_params_file))

    except Exception as e:
        print(f"An error occurred during remote command execution: {e}")


def send_file_to_remote(ssh_client: SSHClient, local_path: str, remote_path: str) -> None:
    """
    Sends a file to the remote via sftp.

    :param ssh_client: The active SSH session.
    :param local_path: The local file to upload.
    :param remote_path: The remote file to upload to.
    """
    try:
        sftp: SFTPClient = ssh_client.open_sftp()
    except Exception as e:
        print("Error opening sftp", e)
    try:
        sftp.put(local_path, remote_path)
    except Exception as e:
        print("Error putting to slurm", e)
        exit(1)


def run_remote_python_script(ssh_client: SSHClient, remote_path: str):
    """
    Run a python script on the remote.

    :param ssh_client: The active SSH session.
    :param remote_path: The remote file to run.
    """
    _, stdout, stderr = ssh_client.exec_command(f"python3 {remote_path}")
    stdout.channel.recv_exit_status()  # Wait for the command to complete
    print("Started script")
    error_message = stderr.read().decode()
    if error_message:
        print(f"Error running script: {error_message}")


def remove_remote_file(ssh_client: SSHClient, remote_path: str):
    """
    Remove a file on the remote.

    :param ssh_client: The active SSH session.
    :param remote_path: The remote file to delete.
    """
    _, stdout, stderr = ssh_client.exec_command(f"rm {remote_path}")
    stdout.channel.recv_exit_status()  # Wait for the command to complete
    print("Removed the script")
    error_message = stderr.read().decode()
    if error_message:
        print(f"Error removing script: {error_message}")
