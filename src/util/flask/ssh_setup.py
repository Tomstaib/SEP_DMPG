import os
import subprocess
import paramiko
from flask import session
from paramiko.client import SSHClient
from paramiko.rsakey import RSAKey
from paramiko.sftp_client import SFTPClient
from src.util.flask.ssh_params import REMOTE_HOST, REMOTE_KEY_PATH_TEMPLATE, KEY_PATH, COMMENT, PASSPHRASE


def generate_ssh_key(key_path: str, comment: str = "", passphrase: str = ""):
    """
    Generate an SSH key and save it in key_path.

    :param key_path: Where the key should be stored.
    :param comment: Comment for the key.
    :param passphrase: Passphrase for the key.
    """
    ssh_dir: str = os.path.dirname(key_path)
    os.makedirs(ssh_dir, exist_ok=True)

    command: list[str] = [
        "ssh-keygen",
        "-t", "rsa",
        "-b", "4096",
        "-f", key_path,
        "-C", comment,
        "-N", passphrase
    ]

    subprocess.run(command, check=True)
    print(f"SSH key generated at {key_path}")


def send_public_key_to_server(ssh_client: SSHClient, public_key: str, username: str,
                              remote_host: str, remote_key_path: str):
    """
    Send the public SSH key to the server.

    :param ssh_client: Active SSH connection to remote.
    :param public_key: The public SSH key.
    :param username: The username to send the public key to.
    :param remote_host: The remote host to send the public key to.
    :param remote_key_path: The path to the public key on the remote.
    """
    try:
        sftp: SFTPClient = ssh_client.open_sftp()
        try:
            sftp.chdir('.ssh')
        except IOError:
            sftp.mkdir('.ssh')
            sftp.chmod('.ssh', 0o700)  # Mode is important to ensure access

        with sftp.open(remote_key_path, 'a') as authorized_keys_file:
            authorized_keys_file.write(public_key + "\n")
        print(f"Public key added to {username}@{remote_host}:{remote_key_path}")
    finally:
        sftp.close()


def setup_ssh_connection(username: str) -> paramiko.SSHClient:
    """
    Sets up an SSH connection for a user and return the client.

    :param username: The username to connect as.

    :return: The SSH client.

    See also:
        - [generate_ssh_key](../util/flask/ssh_setup.html#generate_ssh_key): Generate an SSH key and save it.
        - [send_public_key_to_server](../util/flask/ssh_setup.html#send_public_key_to_server): Send the public key to the server.
    """
    # Check if the SSH key already exists
    if os.path.exists(KEY_PATH):
        print(f"SSH key already exists at {KEY_PATH}. Skipping key generation.")
    else:
        generate_ssh_key(KEY_PATH, COMMENT, PASSPHRASE)

    pub_key_path: str = f"{KEY_PATH}.pub"
    with open(pub_key_path, "r") as pub_key_file:
        public_key: str = pub_key_file.read()

    remote_password: str = session.get('remote_password')

    ssh_client: SSHClient = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if remote_password:
        try:
            ssh_client.connect(REMOTE_HOST, username=username, password=remote_password)
            remote_key_path: str = REMOTE_KEY_PATH_TEMPLATE.format(user=username)
            send_public_key_to_server(ssh_client, public_key, username, REMOTE_HOST, remote_key_path)
        except paramiko.ssh_exception.AuthenticationException:
            ssh_client.close()

    rsa_key: RSAKey = paramiko.RSAKey(filename=KEY_PATH, password=PASSPHRASE if PASSPHRASE else None)
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(REMOTE_HOST, username=username, pkey=rsa_key)
        print("Connection with RSA key successful")
        return ssh_client
    except Exception as e:
        print(f"Error with ssh_client: {e}")


def close_ssh_connection(ssh_client: paramiko.SSHClient):
    """
    Close the SSH client.

    :param ssh_client: Active SSH connection to remote.
    """
    try:
        if ssh_client:
            ssh_client.close()
            print("SSH connection closed.")
    except Exception as e:
        print(f"Error while closing SSH connection: {e}")
