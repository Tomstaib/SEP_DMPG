from functools import wraps
from flask import Flask, request, redirect, url_for, flash, render_template, session, jsonify
from ssh_setup import setup_ssh_connection
from environment import prepare_env, execute_command, transfer_experiments, manipulate_scenario_path, send_db_key, upload_directory
import os
import json
import paramiko
import threading
from composite_tree import CompositeTree
import logging
import experiments
import requests
from datetime import datetime
import shutil
from paramiko.client import SSHClient
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'
USER_DIR = '/var/www/dmpg_api/user'
user_trees = {}

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
                # else:
                #     flash(f"Folder for user '{username}' already exists.")
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
    return render_template('visualization.html', grafana_url=f"https://131.173.65.76:3000/d/edyvm8igqbg1sb/datenbank-dashboard?orgId=1&var-username={session.get('username')}")  # &var-username={session.get('username')}


"""@app.route('/experimental_environment')
@login_required
def experimental_enviroment():
    file_name = os.path.join(SAVE_DIR, 'runtime_prediction.json')

    if os.path.exists(file_name):
        with open(file_name, 'r') as json_file:
            data = json.load(json_file)
    else:
        data = {}  # Leeres Dictionary, falls die Datei nicht existiert

    return render_template('experimental_environment.html', data=data)"""


@app.route('/experimental_environment', methods=['GET', 'POST'])
@login_required
def experimental_environment():
    username = session.get('username', '').strip()
    user_directory = os.path.join(app.root_path, 'user', username)
    # flash(user_directory)
    configurations = []
    config_data = session.pop('config_data', None)  # Retrieve and remove config_data from session

    # Traverse the user's directory to find configuration files
    for root, dirs, files in os.walk(user_directory):
        for file in files:
            if file.endswith('.json'):
                config_path = os.path.join(root, file)
                # Extract model and scenario names from the path
                parts = os.path.relpath(config_path, user_directory).split(os.sep)
                if len(parts) >= 2:
                    model_name = parts[0]
                    scenario_name = parts[1]
                    configurations.append({
                        'model_name': model_name,
                        'scenario_name': scenario_name,
                        'file_name': file,
                        'file_path': config_path
                    })

    if request.method == 'POST':
        try:
            overwrite_confirmed = request.form.get('overwrite_confirmed', 'false') == 'true'
            # Retrieve original and new model/scenario names
            original_model_name = request.form.get('original_model_name', '').strip()
            original_scenario_name = request.form.get('original_scenario_name', '').strip()
            model_name = request.form.get('model_name', '').strip()
            scenario_name = request.form.get('scenario_name', '').strip()

            # Define the configuration file path
            config_directory = os.path.join('user', username, model_name, scenario_name)
            config_filename = f"{model_name}_{scenario_name}.json"
            config_file_path = os.path.join(config_directory, config_filename)

            # Check if the configuration file already exists
            if os.path.exists(config_file_path) and not overwrite_confirmed:
                # Store form data in session
                session['form_data'] = request.form.to_dict(flat=False)
                flash('A configuration with this model and scenario name already exists.')
                # Pass form_data to the template explicitly
                return render_template('confirm_overwrite.html', form_data=session['form_data'])

            logging.info(f"Processing configuration for user: {username}, model: {model_name}, scenario: {scenario_name}")

            # Dictionary to store file paths for arrival tables
            source_files = {}

            # Process all form inputs, including file uploads
            for key in request.form:
                if key.startswith('name_source_'):
                    unique_id = key.replace('name_', '')  # Extract 'source_X' identifier
                    source_name = request.form[key].strip()

                    # Get the corresponding file for this source
                    file_key = f'arrival_table_file_{unique_id}'
                    arrival_table_file = request.files.get(file_key)

                    # Check for existing arrival table path
                    existing_arrival_table = request.form.get(f'existing_arrival_table_{unique_id}')

                    if arrival_table_file and arrival_table_file.filename.endswith('.csv'):
                        # Save the new CSV file and get its path
                        file_path = experiments.save_arrival_table(arrival_table_file, model_name, scenario_name, source_name, username)
                        source_files[unique_id] = file_path
                        # logging.info(f"New arrival table for {source_name} uploaded: {file_path}")
                    elif existing_arrival_table:
                        # Check if model_name or scenario_name has changed
                        if model_name != original_model_name or scenario_name != original_scenario_name:
                            # Copy the arrival table to the new location
                            new_file_path = experiments.copy_arrival_table(existing_arrival_table, model_name, scenario_name, source_name, username)
                            source_files[unique_id] = new_file_path
                            # logging.info(f"Arrival table for {source_name} copied to new location: {new_file_path}")
                        else:
                            # Use the existing arrival table path
                            source_files[unique_id] = existing_arrival_table
                            # logging.info(f"Using existing arrival table for {source_name}: {existing_arrival_table}")
                    else:
                        logging.warning(f"No arrival table provided for {source_name}")

            # Generate the configuration file using form data and the arrival table paths
            config_json = experiments.generate_simulation_configuration(request.form, source_files)
            logging.info(f"Configuration successfully generated.")
            # flash('Trying to save')

            # Save the configuration file
            experiments.save_config_file(config_json, os.path.join(user_directory, model_name, scenario_name), f"{model_name}_{scenario_name}.json")
            flash('Configuration successfully generated')

            # Clear form data from session after successful processing
            session.pop('form_data', None)

            return redirect(url_for('experimental_environment'))

        except Exception as e:
            logging.error(f"Error processing configuration: {e}")
            flash(f'Error processing configuration: {e}')
            return redirect(url_for('experimental_environment'))

    else:
        # Check if there's form data in the session to restore
        form_data = session.pop('form_data', None)
        return render_template('experimental_environment.html', configurations=configurations, config_data=config_data,
                               form_data=form_data)


@app.route('/cancel_overwrite')
@login_required
def cancel_overwrite():
    flash('Configuration generation canceled.')
    return redirect(url_for('experimental_environment'))



@app.route('/load_configuration', methods=['POST'])
@login_required
def load_configuration():
    username = session.get('username', '').strip()
    selected_config_path = request.form.get('config_file')

    # Ensure the selected configuration is within the user's directory
    user_directory = os.path.join(app.root_path, 'user', username)

    if not selected_config_path.startswith(user_directory):
        flash('Invalid configuration selected.')
        return redirect(url_for('experimental_environment'))

    # Load the configuration file
    try:
        with open(selected_config_path, 'r') as f:
            config_data = json.load(f)
        # Store the configuration data in the session or pass it to the template
        session['config_data'] = config_data
        return redirect(url_for('experimental_environment'))
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        flash('Error loading configuration.')
        return redirect(url_for('experimental_environment'))


@app.route('/delete_scenario', methods=['POST'])
def delete_scenario():
    scenario_folder = request.form.get('scenario_delete')
    scenario_folder = os.path.join(app.root_path, scenario_folder)

    # Check if the file exists and delete it
    if scenario_folder and os.path.exists(scenario_folder):
        try:
            shutil.rmtree(scenario_folder)
            flash(f"Configuration {scenario_folder} deleted successfully.", 'success')
        except Exception as e:
            flash(f"An error occurred while deleting the configuration: {str(e)}", 'error')
    else:
        flash(f"Selected configuration file {(scenario_folder)} does not exist.", 'error')

    return redirect(url_for('experimental_environment'))


@app.route('/receive_runtime_prediction', methods=['POST'])
def receive_runtime_prediction():
    # Get the 'user' parameter from the URL
    user = request.args.get('user')
    SAVE_DIR = os.path.join(app.root_path, 'user', user)
    # Get the JSON data from the request body
    data = request.get_json()

    if data:
        # Optionally, you can log or use the 'user' parameter
        print(f"Received data from user: {user}")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data['timestamp'] = timestamp
        print(f"Timestamp added: {timestamp}")


        # Save the JSON data to a file
        file_name = os.path.join(SAVE_DIR, f'{user}_runtime_prediction.json')  # Save the file with the user's name
        with open(file_name, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        return jsonify({"status": "success", "user": user}), 200
    else:
        return jsonify({"status": "failed", "reason": "No JSON data received"}), 400

@app.route('/show_runtime_prediction')
@login_required
def show_runtime_prediction():
    user = session.get('username')
    file_path = f'/var/www/dmpg_api/user/{user}/{user}_runtime_prediction.json'

    # Check if file exists
    if os.path.exists(file_path):
        # Load the file
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
    else:
        data = None # If no runtime prediction

    return render_template('runtime_prediction.html', user=user, data=data)

@app.route('/prepare-env', methods=['POST'])
@login_required
def prepare_env_route():
    try:
        prepare_env(session.get('username'))
        ssh_client = setup_ssh_connection(session.get('username'))
        transfer_experiments(ssh_client, os.path.join(USER_DIR, session.get('username')), session.get('username'))
        send_db_key(ssh_client, session.get('username'))
        flash("Environment preparation started successfully.")
    except Exception as e:
        print(f"Error: {e}")
        flash(f"An error occurred: {e}")
    finally:
        ssh_client.close()

    # Redirect back to the new_job page after processing
    return redirect(url_for('submit_job'))


@app.route('/submit_job', methods=['GET', 'POST'])
@login_required
def submit_job():
    global user_trees
    accounts = []
    selected_account = None
    username = session.get('username')  # Hole den Benutzernamen aus der Session
    ssh_client = setup_ssh_connection(username)
    jwt_token = execute_command(ssh_client, 'scontrol token lifespan=9999')
    jwt_token = jwt_token[0].split('=')[1]

    # Benutzerverzeichnis
    user_directory = os.path.join(app.root_path, 'user', username)

    # Finde alle JSON-Dateien im Benutzerverzeichnis
    json_files = find_json_files(user_directory)

    # Benutzer-spezifischen Composite Tree initialisieren, falls er noch nicht existiert
    if username not in user_trees:
        user_trees[username] = None  # Kein Tree erstellt

    try:
        # Zähle die Compute Nodes im Baum, wenn der Baum existiert
        num_compute_nodes = 0
        if user_trees[username] is not None:
            root = user_trees[username]  # Hol dir die Wurzel des Benutzers
            num_compute_nodes = CompositeTree.count_compute_nodes(root)

        # SSH-Befehl, um die Slurm-Accounts des Benutzers abzurufen
        stdout, stderr = execute_command(setup_ssh_connection(username),
                                         f"sacctmgr show assoc user={username} format=Account%30")
        lines = stdout.splitlines()
        if len(lines) > 2:
            accounts = [line.strip() for line in lines[2:] if line.strip()]

        if request.method == 'POST':
            # Handle Composite Tree creation
            if 'create_tree' in request.form:
                num_children = int(request.form.get('num_children'))
                depth_of_tree = int(request.form.get('depth_of_tree'))

                # Erstelle den Benutzer-spezifischen Composite Tree
                user_trees[username] = CompositeTree.create_custom_composite_tree_with_params(num_children,
                                                                                              depth_of_tree)

                flash("Composite Tree created successfully.")
                return redirect(url_for('submit_job'))  # Neu laden, um die Anzahl der Compute Nodes zu aktualisieren

            # Handle Simulation start
            elif 'start_simulation' in request.form:
                # Prüfen, ob der Benutzer einen Baum erstellt hat und ob dieser mindestens einen Compute Node enthält
                if user_trees[username] is None:
                    flash("Please create a Composite Tree first.")
                    return redirect(url_for('submit_job'))

                # Hol den aktuellen Baum des Benutzers
                root = user_trees[username]

                # Prüfen, ob der Baum mindestens einen Compute Node enthält
                num_compute_nodes = CompositeTree.count_compute_nodes(root)
                if num_compute_nodes < 1:
                    flash("Your tree must contain at least one compute node to start the simulation.")
                    return redirect(url_for('submit_job'))

                # Simulationsparameter abrufen
                selected_account = request.form.get('account')
                num_replications = int(request.form.get('num_replications'))
                num_compute_nodes = int(request.form.get('num_compute_nodes'))
                model_script = request.form.get('model_script')
                manipulated_model_script = manipulate_scenario_path(model_script)
                time_limit = int(request.form.get('time_limit'))
                slurm_username = session.get('username')
                num_replications = round(num_replications / num_compute_nodes)

                # Simulation in einem Thread starten
                def start_simulation_in_thread(num_replications, slurm_account, slurm_username, model_script,
                                               time_limit):

                    if user_trees[username] is not None:
                        root = user_trees[username]
                        root.distribute_and_compute(
                            model=model_script,
                            minutes=time_limit,
                            num_replications=num_replications,
                            slurm_account=slurm_account,
                            model_script=manipulated_model_script,
                            time_limit=time_limit,
                            slurm_username=slurm_username,
                            jwt_token=jwt_token
                        )

                        # Nachdem die Simulation abgeschlossen wurde, lösche den Baum des Benutzers
                        del user_trees[username]  # Benutzer-spezifischen Baum löschen
                        print(f"All trees of the user {username} have been deleted.")

                    else:
                        print("No Composite Tree available for the simulation.")

                simulation_thread = threading.Thread(target=start_simulation_in_thread, args=(
                    num_replications, selected_account, slurm_username, model_script, time_limit
                ))
                simulation_thread.start()

                flash("Simulation started successfully. All trees have been deleted.")
                return redirect(url_for('show_runtime_prediction'))

    except Exception as e:
        print(f"Error: {e}")
        flash(f"An error occurred: {e}")

    # Render template und übergebe die JSON-Dateien sowie die Anzahl der Compute Nodes
    return render_template('submit_job.html', accounts=accounts, selected_account=selected_account,
                           num_compute_nodes=num_compute_nodes, json_files=json_files)


def find_json_files(directory):
    """
    Diese Funktion durchsucht nur die Unterverzeichnisse eines Verzeichnisses rekursiv nach .json-Dateien,
    jedoch nicht das Verzeichnis selbst.
    """
    json_files = []
    for root, dirs, files in os.walk(directory):
        # Überspringe das oberste Verzeichnis und gehe nur in die Unterverzeichnisse
        if root == directory:
            continue
        for file in files:
            if file.endswith('.json'):  # Überprüfen, ob es eine JSON-Datei ist
                full_path = os.path.join(root, file)
                json_files.append({
                    'filename': file,  # Nur den Dateinamen speichern
                    'full_path': full_path  # Den vollständigen Pfad speichern
                })
    return json_files


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

