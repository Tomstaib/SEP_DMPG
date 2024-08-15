import sys

from ssh_with_parameters import transfer_folder, create_ssh_client

ssh = create_ssh_client("imt-sep-001.lin.hs-osnabrueck.de", 22, "sep", "oishooX2iefeiNai")

transfer_folder(ssh, sys.argv[1], "~/test_transfer")
