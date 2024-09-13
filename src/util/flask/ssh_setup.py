import os
import subprocess
import paramiko
from flask import session

REMOTE_HOST = "hpc.hs-osnabrueck.de"
REMOTE_KEY_PATH_TEMPLATE = "/home/{user}/.ssh/authorized_keys"
KEY_PATH = os.path.expanduser("~/.ssh/id_rsa_tunnel_to_zielserver")
COMMENT = "distributed_server@sep"
PASSPHRASE = ""  # Optional: Set passphrase, or keep empty for no passphrase


def generate_ssh_key(key_path, comment="", passphrase=""):
    ssh_dir = os.path.dirname(key_path)
    os.makedirs(ssh_dir, exist_ok=True)

    command = [
        "ssh-keygen",
        "-t", "rsa",
        "-b", "4096",
        "-f", key_path,
        "-C", comment,
        "-N", passphrase
    ]

    subprocess.run(command, check=True)
    print(f"SSH key generated at {key_path}")


def send_public_key_to_server(ssh_client, public_key, username, remote_host, remote_key_path):
    try:
        sftp = ssh_client.open_sftp()
        try:
            sftp.chdir('.ssh')
        except IOError:
            sftp.mkdir('.ssh')
            sftp.chmod('.ssh', 0o700)

        with sftp.open(remote_key_path, 'a') as authorized_keys_file:
            authorized_keys_file.write(public_key + "\n")
        print(f"Public key added to {username}@{remote_host}:{remote_key_path}")
    finally:
        sftp.close()


def setup_ssh_connection(username) -> paramiko.SSHClient:
    # Check if the SSH key already exists
    if os.path.exists(KEY_PATH):
        print(f"SSH key already exists at {KEY_PATH}. Skipping key generation.")
    else:
        generate_ssh_key(KEY_PATH, COMMENT, PASSPHRASE)

    pub_key_path = f"{KEY_PATH}.pub"
    with open(pub_key_path, "r") as pub_key_file:
        public_key = pub_key_file.read()

    remote_password = session.get('remote_password')

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(REMOTE_HOST, username=username, password=remote_password)
        remote_key_path = REMOTE_KEY_PATH_TEMPLATE.format(user=username)
        send_public_key_to_server(ssh_client, public_key, username, REMOTE_HOST, remote_key_path)
    except paramiko.ssh_exception.AuthenticationException:
        ssh_client.close()

    # rsa_key = paramiko.RSAKey(filename=KEY_PATH, password=PASSPHRASE)
    # Ensure RSAKey is loaded correctly
    rsa_key = paramiko.RSAKey(filename=KEY_PATH, password=PASSPHRASE if PASSPHRASE else None)
    ssh_client = paramiko.SSHClient()  # Reinitialize the client
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(REMOTE_HOST, username=username, pkey=rsa_key)
        print("Connection with RSA key successful")
        return ssh_client
    except Exception as e:
        print(f"Error with ssh_client: {e}")

def close_ssh_connection(ssh_client: paramiko.SSHClient):
    try:
        if ssh_client:
            ssh_client.close()
            print("SSH connection closed.")
    except Exception as e:
        print(f"Error while closing SSH connection: {e}")
