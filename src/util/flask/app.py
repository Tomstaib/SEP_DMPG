import logging
from functools import wraps
from flask import Flask, request, redirect, url_for, flash, render_template, session, jsonify
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

@app.route('/experimental_environment', methods=['GET', 'POST'])
@login_required
def experimental_environment():
    if request.method == 'POST':
        try:
            # Get user, scenario, and model details
            username = session.get('username', '').strip()
            scenario_name = request.form.get('scenario_name', '').strip()
            model_name = request.form.get('model_name', '').strip()

            logging.info(f"Starting experimental environment for user: {username}, model: {model_name}, scenario: {scenario_name}")

            # Dictionary to store file paths for uploaded CSVs
            source_files = {}

            # Process all form inputs, including file uploads
            for key in request.form:
                if key.startswith('name_source_'):
                    unique_id = key.replace('name_', '')  # Extract 'source_X' identifier
                    source_name = request.form[key].strip()

                    # Get the corresponding file for this source
                    file_key = f'arrival_table_file_{unique_id}'
                    arrival_table_file = request.files.get(file_key)

                    if arrival_table_file and arrival_table_file.filename.endswith('.csv'):
                        # Save the CSV file and get its path
                        file_path = experiments.save_arrival_table(arrival_table_file, model_name, scenario_name, source_name, username)
                        # Store the file path in the dictionary using the unique_id
                        source_files[unique_id] = file_path
                        logging.info(f"File for {source_name} uploaded successfully: {file_path}")
                    else:
                        logging.warning(f"No valid CSV file uploaded for {source_name}")

            # Generate the configuration file using form data and the CSV file paths
            config_json = experiments.generate_simulation_configuration(request.form, source_files)
            logging.info(f"Configuration successfully generated: {config_json}")
            save_config_file(config_json, os.path.join('user', username, model_name, scenario_name), f"{model_name}_{scenario_name}.json")
            flash('Configuration successfully generated')

            return redirect(url_for('experimental_environment'))

        except Exception as e:
            logging.error(f"Error generating configuration: {e}")
            flash(f'Error generating configuration: {e}')
            return redirect(url_for('experimental_environment'))

    # Handle the GET request to load the page
    return render_template('experimental_environment.html')




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
