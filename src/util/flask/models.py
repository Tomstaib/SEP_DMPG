from flask import session
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, ssh_client=None):
        self.id = id
        self.ssh_client = ssh_client

    @staticmethod
    def get(user_id):
        # Versuch, den SSH-Client aus der Sitzung zu laden
        ssh_client = session.get('ssh_client')
        return User(user_id, ssh_client)

    def close_ssh_connection(self):
        if self.ssh_client:
            self.ssh_client.close()
            session.pop('ssh_client', None)  # Entfernen Sie den Client aus der Sitzung
