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
    :return: True if successful, False otherwise
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

    try:
        subprocess.run(command, check=True)
        print(f"SSH key generated at {key_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating SSH key: {e}")
        return False


def send_public_key_to_server(ssh_client, public_key, remote_user, remote_host, remote_key_path):
    """
    Send the public key to the server and add it to the authorized_keys file.
    :return: True if successful, False otherwise
    """
    sftp = None
    try:
        sftp = ssh_client.open_sftp()
        try:
            sftp.chdir('.ssh')
        except IOError:
            sftp.mkdir('.ssh')
            sftp.chmod('.ssh', 0o700)

        try:
            with sftp.open(remote_key_path, 'a') as authorized_keys_file:
                authorized_keys_file.write(public_key + "\n")
            print(f"Public key added to {remote_user}@{remote_host}:{remote_key_path}")
            return True
        except Exception as e:
            print(f"Error adding public key to {remote_key_path}: {e}")
            return False
    except Exception as e:
        print(f"Error sending public key: {e}")
        return False
    finally:
        if sftp:
            sftp.close()


def main(ssh_client=None, remote_password=None):
    if ssh_client is None:
        ssh_client = paramiko.SSHClient()

    # Check if the SSH key already exists
    if os.path.exists(KEY_PATH):
        print(f"SSH key already exists at {KEY_PATH}. Skipping key generation.")
    else:
        if not generate_ssh_key(KEY_PATH, COMMENT, PASSPHRASE):
            return

    pub_key_path = f"{KEY_PATH}.pub"
    try:
        with open(pub_key_path, "r") as pub_key_file:
            public_key = pub_key_file.read()
    except FileNotFoundError as e:
        print(f"Error reading public key: {e}")
        return

    if remote_password is None:
        if sys.stdin.isatty():
            print("stdin is interactive, prompting for password")
            remote_password = getpass(prompt=f'SSH Password for the server: ')
            print("Password input received")
        else:
            print("stdin is not interactive, cannot prompt for password")
            return

    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(REMOTE_HOST, username=REMOTE_USER, password=remote_password)
        print(REMOTE_KEY_PATH)
        if not send_public_key_to_server(ssh_client, public_key, REMOTE_USER, REMOTE_HOST, REMOTE_KEY_PATH):
            return
    except Exception as e:
        print(f"Error with SSH connection using password: {e}")
        return
    finally:
        ssh_client.close()

    

if __name__ == "__main__":  # pragma: no cover
    main()
