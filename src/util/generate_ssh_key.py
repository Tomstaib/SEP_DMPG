import subprocess
import os
import sys
from getpass import getpass
import paramiko

REMOTE_USER = "sep"
REMOTE_HOST = "imt-sep-001.lin.hs-osnabrueck.de"
REMOTE_KEY_PATH = f"/home/{REMOTE_USER}/.ssh/authorized_keys"
KEY_PATH = os.path.expanduser("~/.ssh/id_rsa_tunnel_to_server")
COMMENT = "distributed_server@sep"  # Comment or identifier for the key
PASSPHRASE = ""  # Optional: Set passphrase, or keep empty for no passphrase


def generate_ssh_key(key_path, comment="", passphrase=""):
    """
    Generate an SSH key pair using ssh-keygen.

    :param key_path: Path where the SSH key will be saved (without extension).
    :param comment: Comment to be included in the SSH public key.
    :param passphrase: Passphrase for the SSH private key (empty for no passphrase).
    :return: None
    """
    # Ensure the .ssh directory exists
    ssh_dir = os.path.dirname(key_path)
    os.makedirs(ssh_dir, exist_ok=True)

    # Generate the SSH key pair
    command = [
        "ssh-keygen",
        "-t", "rsa",  # Use RSA key type
        "-b", "4096",  # Key length in bits
        "-f", key_path,  # Path to save the key
        "-C", comment,  # Comment (usually email or identifier)
        "-N", passphrase  # Passphrase (empty for no passphrase)
    ]

    subprocess.run(command, check=True)
    print(f"SSH key generated at {key_path}")


def send_public_key_to_server(ssh_client, public_key, remote_user, remote_host, remote_key_path):
    """
    Send the public key to the server and add it to the authorized_keys file.
    """
    try:
        sftp = ssh_client.open_sftp()
        try:
            # Check if the .ssh directory exists on the remote server
            sftp.chdir('.ssh')
        except IOError:
            # If it doesn't exist, create it
            sftp.mkdir('.ssh')
            sftp.chmod('.ssh', 0o700)

        # Append the public key to the authorized_keys file
        with sftp.open(remote_key_path, 'a') as authorized_keys_file:
            authorized_keys_file.write(public_key + "\n")
        print(f"Public key added to {remote_user}@{remote_host}:{remote_key_path}")
    finally:
        sftp.close()


def main():
    # Check if the SSH key already exists
    if os.path.exists(KEY_PATH):
        print(f"SSH key already exists at {KEY_PATH}. Skipping key generation.")
    else:
        # Generate the SSH key
        generate_ssh_key(KEY_PATH, COMMENT, PASSPHRASE)

    # Read the public key
    pub_key_path = f"{KEY_PATH}.pub"
    with open(pub_key_path, "r") as pub_key_file:
        public_key = pub_key_file.read()

    try:
        # Check if input can be received
        if sys.stdin.isatty():
            print("stdin is interactive, prompting for password")
            remote_password: str = getpass(prompt=f'SSH Password for the server: ')
            print("Password input received")
        else:
            print("stdin is not interactive, cannot prompt for password")
            return
    except Exception as e:
        print(f"Error with getpass: {e}")
        return

    # Connect to the remote server
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # First-time connection using password to upload the public key
        ssh_client.connect(REMOTE_HOST, username=REMOTE_USER, password=remote_password)
        print(REMOTE_KEY_PATH)
        send_public_key_to_server(ssh_client, public_key, REMOTE_USER, REMOTE_HOST, REMOTE_KEY_PATH)
    finally:
        ssh_client.close()

    rsa_key = paramiko.RSAKey(filename=KEY_PATH, password=PASSPHRASE)  # necessary because of paramiko issue
    try:
        ssh_client.connect(REMOTE_HOST, username=REMOTE_USER, pkey=rsa_key)
        print("Connection with rsa successful")
    except Exception as e:
        print(f"Error with ssh_client: {e}")

    # Close the SSH connection
    ssh_client.close()



if __name__ == "__main__":
    main()
