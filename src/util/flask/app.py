import logging
import shutil
from functools import wraps
from flask import Flask, request, redirect, url_for, flash, render_template, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from ssh_setup import setup_ssh_connection
from environment import prepare_env
import os
import json
import paramiko
import experiments
from util.flask.experiments import save_config_file

app = Flask(__name__)
app.secret_key = 'your_secret_key'
SAVE_DIR = '/received_data'
USER_DIR = '/user'

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

"""@app.route('/experimental_environment', methods=['GET', 'POST'])
@login_required
def experimental_environment():
    if request.method == 'POST':
        # This part handles the config generation based on form submission
        config_filename = experiments.generate_config(request.form, session['username'])
        flash(f"Configuration generated and saved to {config_filename}!")
        return redirect(url_for('experimental_environment'))

    # For GET requests, load the existing runtime prediction
    data = experiments.load_runtime_prediction()  # Use the existing data loading logic
    return render_template('experimental_environment.html', data=data)"""


"""@app.route('/experimental_environment', methods=['GET','POST'])
@login_required
def experimental_environment():
    if request.method == 'POST':
        try:
            # Retrieve the file from the file input
            arrival_table_file = request.files.get('arrival_table_file')

            config_filename = experiments.generate_config(request.form, session['username'])

            # Handle the file upload if present
            if arrival_table_file and arrival_table_file.filename.endswith('.csv'):
                # Save the file to a desired location
                filename = "test_" + arrival_table_file.filename
                file_path = os.path.join('uploads', filename)  # Adjust 'uploads' to your directory
                arrival_table_file.save(file_path)


                flash(f'File uploaded successfully: {filename}')
            else:
                flash('Invalid file format. Only CSV files are allowed.')
            flash(f'Configuration saved to {config_filename}')
            return redirect(url_for('experimental_environment'))
        except Exception as e:
            flash(f'Error generating configuration: {e}')

    # For GET requests, load the existing runtime prediction
    data = experiments.load_runtime_prediction()  # Use the existing data loading logic
    return render_template('experimental_environment.html', data=data)"""


"""@app.route('/experimental_environment', methods=['GET', 'POST'])
@login_required
def experimental_environment():
    if request.method == 'POST':
        try:
            # Get user, scenario, and model details
            username = session.get('username', '').strip()
            scenario_name = request.form.get('scenario_name', '').strip()
            model_name = request.form.get('model_name', '').strip()

            # Dictionary to store file paths for uploaded CSVs
            source_files = {}

            # Process all form inputs, including file uploads
            for key in request.form:
                if key.startswith('source_name_'):
                    source_index = key.split('_')[-1]
                    source_name = request.form[key].strip()

                    # Get the corresponding file for this source
                    file_key = f'arrival_table_file_{source_index}'
                    arrival_table_file = request.files.get(file_key)

                    # Handle the file upload if a valid CSV file is present
                    if arrival_table_file and arrival_table_file.filename.endswith('.csv'):
                        # Create the directory structure based on user/model/scenario
                        base_directory = os.path.join('user', username, 'arrival_tables', model_name, scenario_name)
                        os.makedirs(base_directory, exist_ok=True)

                        # Generate a secure filename and prepend the source name
                        filename = secure_filename(arrival_table_file.filename)
                        filename_with_source = f"{source_name}_{filename}"

                        # Save the file to the directory
                        file_path = os.path.join(base_directory, filename_with_source)
                        arrival_table_file.save(file_path)

                        # Store the file path in the dictionary for later use in config generation
                        source_files[source_name] = file_path

                        flash(f'File for {source_name} uploaded successfully: {filename_with_source}')
                    else:
                        flash(f'No valid CSV file uploaded for {source_name}')

            # Now generate the configuration file using form data and uploaded file paths
            config_filename = experiments.generate_simulation_configuration(request.form)
            flash(f'Configuration saved to {config_filename}')

            return redirect(url_for('experimental_environment'))

        except Exception as e:
            flash(f'Error generating configuration: {e}')
            return redirect(url_for('experimental_environment'))

    # Handle the GET request to load the page
    data = experiments.load_runtime_prediction()
    return render_template('experimental_environment.html', data=data)"""

"""@app.route('/experimental_environment', methods=['GET', 'POST'])
@login_required
def experimental_environment():
    username = session.get('username', '').strip()
    user_directory = os.path.join('user', username)
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
                        logging.info(f"New arrival table for {source_name} uploaded: {file_path}")
                    elif existing_arrival_table:
                        # Check if model_name or scenario_name has changed
                        if model_name != original_model_name or scenario_name != original_scenario_name:
                            # Copy the arrival table to the new location
                            new_file_path = experiments.copy_arrival_table(existing_arrival_table, model_name, scenario_name, source_name, username)
                            source_files[unique_id] = new_file_path
                            logging.info(f"Arrival table for {source_name} copied to new location: {new_file_path}")
                        else:
                            # Use the existing arrival table path
                            source_files[unique_id] = existing_arrival_table
                            logging.info(f"Using existing arrival table for {source_name}: {existing_arrival_table}")
                    else:
                        logging.warning(f"No arrival table provided for {source_name}")

            # Generate the configuration file using form data and the arrival table paths
            config_json = experiments.generate_simulation_configuration(request.form, source_files)
            logging.info(f"Configuration successfully generated.")

            # Save the configuration file
            save_config_file(config_json, os.path.join('user', username, model_name, scenario_name), f"{model_name}_{scenario_name}.json")
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
                               form_data=form_data)"""


@app.route('/experimental_environment', methods=['GET', 'POST'])
@login_required
def experimental_environment():
    username = session.get('username', '').strip()
    user_directory = os.path.join(app.root_path, 'user', username)

    # Check if the user directory exists
    if not os.path.exists(user_directory):
        logging.error(f"Directory {user_directory} does not exist.")
        flash(f"User directory for {username} does not exist.")
        return redirect(url_for('experimental_environment'))

    configurations = []
    config_data = session.pop('config_data', None)  # Retrieve and remove config_data from session

    # Traverse the user's directory to find configuration files
    for root, dirs, files in os.walk(user_directory):
        for file in files:
            if file.endswith('.json'):
                config_path = os.path.join(root, file)
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
            original_model_name = request.form.get('original_model_name', '').strip()
            original_scenario_name = request.form.get('original_scenario_name', '').strip()
            model_name = request.form.get('model_name', '').strip()
            scenario_name = request.form.get('scenario_name', '').strip()

            config_directory = os.path.join('user', username, model_name, scenario_name)
            config_filename = f"{model_name}_{scenario_name}.json"
            config_file_path = os.path.join(config_directory, config_filename)

            if os.path.exists(config_file_path) and not overwrite_confirmed:
                session['form_data'] = request.form.to_dict(flat=False)
                flash('A configuration with this model and scenario name already exists.')
                return render_template('confirm_overwrite.html', form_data=session['form_data'])

            logging.info(f"Processing configuration for user: {username}, model: {model_name}, scenario: {scenario_name}")

            # Dictionary to store file paths for arrival tables
            source_files = {}

            for key in request.form:
                if key.startswith('name_source_'):
                    unique_id = key.replace('name_', '')  # Extract 'source_X' identifier
                    source_name = request.form[key].strip()
                    file_key = f'arrival_table_file_{unique_id}'
                    arrival_table_file = request.files.get(file_key)
                    existing_arrival_table = request.form.get(f'existing_arrival_table_{unique_id}')

                    if arrival_table_file and arrival_table_file.filename.endswith('.csv'):
                        file_path = experiments.save_arrival_table(arrival_table_file, model_name, scenario_name, source_name, username)
                        source_files[unique_id] = file_path
                        logging.info(f"New arrival table for {source_name} uploaded: {file_path}")
                    elif existing_arrival_table:
                        if model_name != original_model_name or scenario_name != original_scenario_name:
                            new_file_path = experiments.copy_arrival_table(existing_arrival_table, model_name, scenario_name, source_name, username)
                            source_files[unique_id] = new_file_path
                            logging.info(f"Arrival table for {source_name} copied to new location: {new_file_path}")
                        else:
                            source_files[unique_id] = existing_arrival_table
                            logging.info(f"Using existing arrival table for {source_name}: {existing_arrival_table}")
                    else:
                        logging.warning(f"No arrival table provided for {source_name}")

            # Generate the configuration file using form data and the arrival table paths
            config_json = experiments.generate_simulation_configuration(request.form, source_files)
            logging.info(f"Configuration successfully generated.")
            flash('Trying to save')
            save_config_file(config_json, os.path.join('user', username, model_name, scenario_name), f"{model_name}_{scenario_name}.json")
            flash('Configuration successfully generated')

            session.pop('form_data', None)
            return redirect(url_for('experimental_environment'))

        except Exception as e:
            logging.error(f"Error processing configuration: {e}")
            flash(f'Error processing configuration: {e}')
            return redirect(url_for('experimental_environment'))

    else:
        form_data = session.pop('form_data', None)
        return render_template('experimental_environment.html', configurations=configurations, config_data=config_data,
                               form_data=form_data)


@app.route('/download/<path:filename>')
@login_required
def download_file(filename):
    username = session.get('username', '').strip()
    user_directory = os.path.join(app.root_path, 'user', username)

    # Use Flask's send_from_directory to send the requested file
    try:
        return send_from_directory(user_directory, filename, as_attachment=True)
    except FileNotFoundError:
        flash(f"File {filename} not found.")
        return redirect(url_for('experimental_environment'))


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
    user_directory = os.path.join('user', username)
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

@app.route('/generate_config', methods=['GET', 'POST'])
@login_required
def generate_config_route():
    if request.method == 'POST':
        # Call the `generate_config` function from the `experiments` module
        config_filename = experiments.generate_config(request.form, session['username'])
        flash(f"Configuration generated and saved to {config_filename}!")
        return redirect(url_for('dashboard'))

    return render_template('generate_config.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
    logging.basicConfig(level=logging.DEBUG)
