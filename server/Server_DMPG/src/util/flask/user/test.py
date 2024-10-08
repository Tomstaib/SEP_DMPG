from src.util.flask.environment import transfer_experiments
from src.util.flask.ssh_setup import setup_ssh_connection
from src.util.flask.app import send_and_delete_db
import paramiko

ssh_client = paramiko.SSHClient()

ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname="hpc.hs-osnabrueck.de", username="thoadelt", password="XzCxL8vxQD77Te")

# transfer_experiments(ssh_client,
#                     r"E:/projects/SEP_DMPG/src/util/flask/user/thoadelt",
#                     "thoadelt")

send_and_delete_db(ssh_client)

ssh_client.close()
