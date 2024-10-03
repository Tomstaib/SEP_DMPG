import os

REMOTE_HOST = "hpc.hs-osnabrueck.de"
REMOTE_KEY_PATH_TEMPLATE = "/home/{user}/.ssh/authorized_keys"
KEY_PATH = os.path.expanduser("~/.ssh/id_rsa_tunnel_to_zielserver")
COMMENT = "distributed_server@sep"
PASSPHRASE = ""  # Optional: Set passphrase, or keep empty for no passphrase
