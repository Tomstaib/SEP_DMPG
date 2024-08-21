import paramiko
import logging

def ssh_login(host, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password)
        logging.debug(f'Successfully connected to {host} as {username}')
        return client
    except paramiko.AuthenticationException:
        logging.error('Authentication failed, please verify your credentials')
    except paramiko.SSHException as sshException:
        logging.error(f'Unable to establish SSH connection: {sshException}')
    except paramiko.BadHostKeyException as badHostKeyException:
        logging.error(f'Unable to verify server\'s host key: {badHostKeyException}')
    except Exception as e:
        logging.error(f'Exception in connecting to SSH: {e}')
    return None
