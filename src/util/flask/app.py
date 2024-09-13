from functools import wraps
from flask import Flask, request, redirect, url_for, flash, render_template, session, jsonify
from ssh_setup import setup_ssh_connection
from environment import prepare_env
import os
import json
import paramiko

app = Flask(__name__)
app.secret_key = 'your_secret_key'
SAVE_DIR = '/var/www/dmpg_api/received_data'
USER_DIR = '/var/www/dmpg_api/user'

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You need to log in first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            # Basic validation (ensure username and password are provided)
            if not username or not password:
                flash('Username and password are required.')
                return render_template('login.html')

            # Storing username in the session
            session['username'] = username

            # Storing remote password for SSH in the session (ensure this is necessary and secure)
            session['remote_password'] = password

            # Attempt to set up SSH connection
            # setup_ssh_connection(username)

            # flash('Login successful and SSH key setup completed.')
            # return redirect(url_for('dashboard'))

	    # Attempt to set up SSH connection
            ssh_client: paramiko.SSHClient = setup_ssh_connection(username)

            flash('Login successful and SSH key setup completed.')
            user_folder = os.path.join(USER_DIR, username)
            try:
                if not os.path.exists(user_folder):
                    # os.makedirs(user_folder)
                    os.makedirs(user_folder, mode=0o755)
                    flash(f"Folder for user '{username}' has been created.")
                else:
                    flash(f"Folder for user '{username}' already exists.")
            except OSError as e:
                flash(f"An error occurred while creating the folder: {e}")
                print(f"Error creating directory: {e}")
                with open("/home/sep/log.txt", "a") as f:
                    f.write(f"{e}")

            ssh_client.close()
            return redirect(url_for('dashboard'))
    except Exception as e:
        # Log the error (optional: integrate with logging framework)
        print(f"An error occurred: {e}")
        with open("/home/sep/log.txt", "a") as f:
            f.write(f"{e}")

        # Flash a message to the user
        flash('An error occurred during the login process. Please try again.')

        # Optionally, redirect back to login or render the login page again with the error message
        return render_template('login.html')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/settings')
@login_required  # Ensure the user is logged in to access this page
def settings():
    return render_template('settings.html')


@app.route('/new_job')
@login_required
def new_job():
    return render_template('new_job.html')

@app.route('/contact')
@login_required
def contact():
    return render_template('contact.html')

@app.route('/visualization')
@login_required
def visualization():
    return render_template('visualization.html')

@app.route('/experimental_environment')
@login_required
def experimental_enviroment():
    file_name = os.path.join(SAVE_DIR, 'runtime_prediction.json')

    if os.path.exists(file_name):
        with open(file_name, 'r') as json_file:
            data = json.load(json_file)
    else:
        data = {}  # Leeres Dictionary, falls die Datei nicht existiert

    return render_template('experimental_environment.html', data=data)

@app.route('/receive_runtime_prediction', methods=['POST'])
def receive_runtime_prediction():
    data = request.get_json() #Message saved as json

    if data:
        file_name = os.path.join(SAVE_DIR, 'runtime_prediction.json')
        with open(file_name, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "failed", "reason": "No JSON data received"}), 400


@app.route('/prepare-env', methods=['POST'])
@login_required
def prepare_env_route():
    try:
        prepare_env()  # Call the function
        flash("Environment preparation started successfully.")
    except Exception as e:
        print(f"Error: {e}")
        flash(f"An error occurred: {e}")

    # Redirect back to the new_job page after processing
    return redirect(url_for('new_job'))
#Test#
@app.route('/upload-json', methods=['POST'])
def upload_json():
    # Überprüfen, ob der Request eine JSON-Datei enthält
    if request.is_json:
        # Lade die JSON-Daten
        data = request.get_json()

        # Verarbeite die Daten (zum Beispiel einfach zurücksenden)
        return jsonify({
            "message": "JSON erfolgreich empfangen",
            "received_data": data
        }), 200
    else:
        return jsonify({
            "error": "Kein JSON im Request gefunden"
        }), 400

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
    logging.basicConfig(level=logging.DEBUG)
