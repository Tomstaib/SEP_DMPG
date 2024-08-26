from flask import Flask, request, session, redirect, url_for, flash, render_template
from ssh_setup import setup_ssh_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hier können Sie die Logik für das Authentifizieren des Benutzers hinzufügen
        # Wenn die Authentifizierung erfolgreich ist:
        session['username'] = username
        session['remote_password'] = password

        # SSH-Schlüssel einrichten und Verbindung testen
        setup_ssh_connection(username)

        flash('Login successful and SSH key setup completed.')
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    # Beispiel-Dashboard-Ansicht
    return f"Welcome {session.get('username')}! You are logged in."


if __name__ == "__main__":
    app.run(debug=True)
