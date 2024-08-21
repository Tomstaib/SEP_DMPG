from flask import Flask, request, render_template, redirect, url_for, flash
import paramiko

app = Flask(__name__)
app.secret_key = 'HDThLH6FVj'  # Ändere das in einen sicheren Schlüssel


def ssh_login(username, password):
    try:
        # Initialisiere den SSH-Client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Ersetze 'hostname' durch den tatsächlichen Hostnamen oder die IP-Adresse
        ssh.connect('hpc.hs-osnabrueck.de', username=username, password=password)

        # Schließe die SSH-Verbindung, falls sie nicht mehr benötigt wird
        ssh.close()
        return True  # Login erfolgreich
    except paramiko.AuthenticationException:
        return False  # Login fehlgeschlagen
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if ssh_login(username, password):
        # Weiterleitung nach erfolgreichem Login
        flash('Login erfolgreich!')
        return redirect(url_for('dashboard'))
    else:
        # Fehlermeldung anzeigen
        flash('Login fehlgeschlagen. Bitte überprüfe deine Anmeldedaten.')
        return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    return "Willkommen im Dashboard!"


if __name__ == "__main__":
    app.run()
