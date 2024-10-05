from functools import wraps
from flask import Flask, request, redirect, url_for, flash, render_template, session, jsonify, Response
from typing import Callable, Any, Optional
from paramiko.client import SSHClient
from werkzeug.datastructures.file_storage import FileStorage
from src.util.flask.ssh_setup import setup_ssh_connection
from src.util.flask.environment import prepare_env, execute_command, transfer_experiments, manipulate_scenario_path, \
    create_db_key_on_remote
import os
import json
import paramiko
import threading
from src.util.flask.composite_tree import CompositeTree, ManagementNode
import logging
from src.util.flask.experiments import save_arrival_table, copy_arrival_table, generate_simulation_configuration, \
    save_config_file
from datetime import datetime
import shutil

app = Flask(__name__)
"""Initialize the flask app."""

app.secret_key = os.getenv('SECRET_KEY')
"""Get the secret key that was exported to environment variables. In PyCharm "Edit Configurations"
or "export SECRET_KEY='super-secret-key'" in your environment. """

USER_DIR = '/var/www/dmpg_api/user'
"""User directory. Each user gets their own subdirectory."""

user_trees: dict[str, Optional[ManagementNode]] = {}
"""Composite tree of each user stored here."""


@app.route('/')
def index() -> Response:
    """
    Redirects to appropriate site if Base-URL is requested.
    """
    if 'username' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


def login_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure that the site is only available to logged-in users. If the username is not present in the
    session, the user will be redirected to the login page.

    :param f: The route function to be decorated,

    :return: Function that wraps the decorated function and ensures only logged-in users can access.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You need to log in first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login() -> Response | str:
    """
    Handles login process. On a GET request the login form is rendered. On a POST request the login is being processed.
    The login will set up an SSH connection and create a user folder. After successful login the user is redirected
    to the dashboard.

    See also:
        - [setup_ssh_connection](../flask/ssh_setup.html#setup_ssh_connection): Function to set up SSH connection.
    """
    login_html: str = 'login.html'

    try:
        if request.method == 'POST':
            username: str = request.form['username']
            password: str = request.form['password']

            if not username or not password:
                flash('Username and password are required.')
                return render_template(login_html)

            # Store username in the session
            session['username']: str = username

            # Store password in session to set up ssh connection. It is deleted afterward.
            session['remote_password']: str = password

            # Attempt to set up SSH connection
            ssh_client: paramiko.SSHClient = setup_ssh_connection(username)

            session.pop('remote_password', None)
            del password

            flash('Login successful and SSH key setup completed.')
            user_folder: str = os.path.join(USER_DIR, username)
            try:
                if not os.path.exists(user_folder):
                    os.makedirs(user_folder, mode=0o755)  # The mode is important so file access is possible
                    flash(f"Folder for user '{username}' has been created.")
            except OSError as e:
                flash(f"An error occurred while creating the folder: {e}")
                print(f"Error creating directory: {e}")
                with open("/home/sep/log.txt", "a") as f:
                    f.write(f"{e}")

            ssh_client.close()
            return redirect(url_for('dashboard'))

    except Exception as e:

        print(f"An error occurred: {e}")
        with open("/home/sep/log.txt", "a") as f:
            f.write(f"{e}")

        flash('An error occurred during the login process. Please try again.')

        # Render login with error message
        return render_template(login_html)

    return render_template(login_html)


@app.route('/dashboard')
@login_required
def dashboard() -> str:
    """
    The dashboard will be rendered. User has to be logged in.

    See also:
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout() -> Response:
    """
    Logs out the current user and redirects to the login page. User has to be logged in.

    See also:
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/settings')
@login_required
def settings() -> str:
    """
    Renders the template for settings. User has to be logged in.

    See also:
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    return render_template('settings.html')


@app.route('/new_job')
@login_required
def new_job() -> str:
    """
    Renders the template for a new job. User has to be logged in.

    See also:
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    return render_template('new_job.html')


@app.route('/contact')
@login_required
def contact() -> str:
    """
    Renders the template for contact. User has to be logged in.

    See also:
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    return render_template('contact.html')


@app.route('/visualization')
@login_required
def visualization() -> (str, str):
    """
    Renders the template for visualization. User has to be logged in.

    :return: The template and the url to grafana with the current username.

    See also:
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    return render_template('visualization.html',
                           grafana_url=f"https://131.173.65.76:3000/d/edyvm8igqbg1sb/datenbank-dashboard?orgId=1&var-username={session.get('username')}")


"""@app.route('/experimental_environment', methods=['GET', 'POST'])
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

            logging.info(
                f"Processing configuration for user: {username}, model: {model_name}, scenario: {scenario_name}")

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
                        file_path = save_arrival_table(arrival_table_file, model_name, scenario_name,
                                                       source_name, username)
                        source_files[unique_id] = file_path
                        # logging.info(f"New arrival table for {source_name} uploaded: {file_path}")
                    elif existing_arrival_table:
                        # Check if model_name or scenario_name has changed
                        if model_name != original_model_name or scenario_name != original_scenario_name:
                            # Copy the arrival table to the new location
                            new_file_path = copy_arrival_table(existing_arrival_table, model_name,
                                                               scenario_name, source_name, username)
                            source_files[unique_id] = new_file_path
                            # logging.info(f"Arrival table for {source_name} copied to new location: {new_file_path}")
                        else:
                            # Use the existing arrival table path
                            source_files[unique_id] = existing_arrival_table
                            # logging.info(f"Using existing arrival table for {source_name}: {existing_arrival_table}")
                    else:
                        logging.warning(f"No arrival table provided for {source_name}")

            # Generate the configuration file using form data and the arrival table paths
            config_json = generate_simulation_configuration(request.form, source_files)
            logging.info("Configuration successfully generated.")
            # flash('Trying to save')

            # Save the configuration file
            save_config_file(config_json, os.path.join(user_directory, model_name, scenario_name),
                             f"{model_name}_{scenario_name}.json")
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
def experimental_environment() -> Any:
    """
    Handle the experiment environment of the current user. For GET requests, it displays the page with the user's
    existing configurations. For POST requests, it processes form data to create or overwrite a configuration.
    User has to be logged in.

    :return: The rendered template or redirect response to the experimental environment page.

    See also:
        - [get_user_configuration](../util/flask/app.html#get_user_configuration): Retrieve all simulation configurations of a user.
        - [get_model_and_scenario_names](../util/flask/app.html#get_model_and_scenario_names): Retrieve model and scenario names.
        - [define_config_paths](../util/flask/app.html#define_config_paths): Define configuration paths.
        - [check_overwrite](../util/flask/app.html#check_overwrite): Check overwrite.
        - [process_form_inputs](../util/flask/app.html#process_form_inputs): Process the (previously entered) form data.
        - [generate_simulation_configuration](../util/flask/experiments.html#generate_simulation_configuration): Generate a configuration file for a scenario.
        - [save_configuration](../util/flask/app.html#save_configuration): Save the configuration file.
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    username: str = session.get('username', '').strip()
    user_directory: str = os.path.join(app.root_path, 'user', username)
    configurations: list[dict[str, Any]] = get_user_configurations(user_directory)
    config_data: Optional[Any] = session.pop('config_data', None)

    if request.method == 'POST':
        try:

            original_model_name, original_scenario_name, model_name, scenario_name = get_model_and_scenario_names(
                request.form)

            _, config_file_path = define_config_paths(username, model_name, scenario_name)

            overwrite_response = check_overwrite(request.form, config_file_path)
            if overwrite_response:
                return overwrite_response

            logging.info(
                f"Processing configuration for user: {username}, model: {model_name}, scenario: {scenario_name}")

            source_files: dict[str, str] = process_form_inputs(request.form, request.files, model_name,
                                                               scenario_name, username, original_model_name,
                                                               original_scenario_name)

            config_json: str = generate_simulation_configuration(request.form, source_files)
            logging.info("Configuration successfully generated.")

            save_configuration(config_json, user_directory, model_name, scenario_name)
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
        form_data: Optional[dict[str, Any]] = session.pop('form_data', None)
        return render_template('experimental_environment.html', configurations=configurations,
                               config_data=config_data, form_data=form_data)


def get_user_configurations(user_directory: str) -> list[dict[str, Any]]:
    """
    Retrieve existing configurations from the current user's directory.

    :param user_directory: The current user's directory.

    :return: A list of dictionaries containing the configurations.
    """
    configurations: list[dict[str, Any]] = []
    for root, dirs, files in os.walk(user_directory):
        for file in files:
            if file.endswith('.json'):
                config_path = os.path.join(root, file)

                # Extract model and scenario names from the path
                parts = os.path.relpath(config_path, user_directory).split(os.sep)
                if len(parts) >= 2:
                    model_name, scenario_name = parts[0], parts[1]
                    configurations.append({
                        'model_name': model_name,
                        'scenario_name': scenario_name,
                        'file_name': file,
                        'file_path': config_path
                    })

    return configurations


def get_model_and_scenario_names(form_data: dict[str, Any]) -> (str, str, str, str):
    """
    Extract original and new model and scenario names from form data.

    :param form_data: The form data from the html input.

    :return: A tuple containing the original and new model and scenario names.
    """
    original_model_name: str = form_data.get('original_model_name', '').strip()
    original_scenario_name: str = form_data.get('original_scenario_name', '').strip()
    model_name: str = form_data.get('model_name', '').strip()
    scenario_name: str = form_data.get('scenario_name', '').strip()
    return original_model_name, original_scenario_name, model_name, scenario_name


def define_config_paths(username: str, model_name: str, scenario_name: str) -> (str, str):
    """
    Define the configuration directory and file paths.

    :param username: The current user's username.
    :param model_name: The model name provided by the user in the html form.
    :param scenario_name: The scenario name provided by the user in the html form.

    :return: A tuple containing the configuration directory and file paths.
    """
    config_directory: str = os.path.join('user', username, model_name, scenario_name)
    config_filename: str = f"{model_name}_{scenario_name}.json"
    config_file_path: str = os.path.join(config_directory, config_filename)
    return config_directory, config_file_path


def check_overwrite(form_data, config_file_path: str) -> Optional[Any]:  # Only any as return because of Optional
    """
    Check if the configuration file already exists and overwrite if user confirmed.

    :param form_data: The form data from the html input.
    :param config_file_path: The configuration file path.

    :return: Either None or a tuple containing the render template and the form data.
    """
    overwrite_confirmed = form_data.get('overwrite_confirmed', 'false') == 'true'

    if os.path.exists(config_file_path) and not overwrite_confirmed:
        # Store form data in session
        session['form_data'] = form_data.to_dict(flat=False)
        flash('A configuration with this model and scenario name already exists.')
        return render_template('confirm_overwrite.html', form_data=session['form_data'])

    return None


def process_form_inputs(form_data: dict[str, Any], files_data: dict[str, FileStorage],
                        model_name: str, scenario_name: str, username: str,
                        original_model_name: str, original_scenario_name: str) -> dict[str, str]:
    """
    Process all form inputs and handle arrival tables for each source.

    :param form_data: The form data from the html input.
    :param files_data: The files uploaded by the user.
    :param model_name: The new model name provided by the user in the html form.
    :param scenario_name: The new scenario name provided by the user in the html form.
    :param username: The current user's username.
    :param original_model_name: The original model name.
    :param original_scenario_name: The original scenario name.

    :return: A dictionary mapping the component IDs to the arrival tables.

    See also:
        - [Source](../core/source.html): Source in a simulation environment.
        - [process_source](../util/flask/app.html#process_source): Process sources and their arrival table.
    """
    source_files: dict[str, str] = {}

    for key in form_data:
        if key.startswith('name_source_'):
            unique_id: str = key.replace('name_', '')
            source_name: Optional[str] = form_data[key].strip()

            file_path: Optional[str] = process_source(unique_id, source_name, form_data, files_data,
                                                      model_name, scenario_name, username, original_model_name,
                                                      original_scenario_name)

            if file_path:
                source_files[unique_id]: str = file_path

    return source_files


def process_source(unique_id: str, source_name: str, form_data: dict[str, Any],
                   files_data: dict[str, FileStorage], model_name: str, scenario_name: str, username: str,
                   original_model_name: str, original_scenario_name: str) -> Optional[str]:
    """
    Process each source and their arrival table. Manipulate the file path if necessary.

    :param unique_id: The unique ID of the source.
    :param source_name: The name of the source.
    :param form_data: The form data from the html input.
    :param files_data: The files uploaded by the user.
    :param model_name: The new model name provided by the user in the html form.
    :param scenario_name: The new scenario name provided by the user in the html form.
    :param username: The current user's username.
    :param original_model_name: The original model name.
    :param original_scenario_name: The original scenario name.

    :return: The file path of the arrival table or None if no arrival table was provided.

    See also:
        - [save_arrival_table](../util/flask/experiments.html#save_arrival_table): Save the provided arrival table.
        - [copy_arrival_table](../util/flask/experiments.html#copy_arrival_table): Copy the provided arrival table to another scenario.
    """
    file_key: str = f'arrival_table_file_{unique_id}'
    arrival_table_file: Optional[FileStorage] = files_data.get(file_key)
    existing_arrival_table: Optional[str] = form_data.get(f'existing_arrival_table_{unique_id}')

    if arrival_table_file and arrival_table_file.filename.endswith('.csv'):
        # Save the new CSV file and get its path
        file_path: str = save_arrival_table(arrival_table_file, model_name, scenario_name, source_name, USER_DIR, username)
        return file_path
    elif existing_arrival_table:
        if model_name != original_model_name or scenario_name != original_scenario_name:
            # Copy the arrival table to the new location
            new_file_path: str = copy_arrival_table(existing_arrival_table, model_name,
                                                    scenario_name, source_name, username)
            return new_file_path
        else:
            # Use the existing arrival table path
            return existing_arrival_table
    else:
        logging.warning(f"No arrival table provided for {source_name}")
        return None


def save_configuration(config_json: str, user_directory: str,
                       model_name: str, scenario_name: str):
    """
    Save the generated configuration file.

    :param config_json: The configuration file in a json form.
    :param user_directory: The user directory path.
    :param model_name: The new model name provided by the user in the html form.
    :param scenario_name: The new scenario name provided by the user in the html form.

    See also:
        - [save_config_file](../util/flask/experiments.html#save_config_file):
    """
    config_directory: str = os.path.join(user_directory, model_name, scenario_name)
    config_filename: str = f"{model_name}_{scenario_name}.json"
    save_config_file(config_json, config_directory, config_filename)


@app.route('/cancel_overwrite')
@login_required
def cancel_overwrite() -> Response:
    """
    Cancel the overwrite of a configuration file. User has to be logged in.

    :return: Redirect to the experimental environment, so it's a response.

    See also:
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    flash('Configuration generation canceled.')
    return redirect(url_for('experimental_environment'))


@app.route('/load_configuration', methods=['POST'])
@login_required
def load_configuration() -> Response:
    """
    Handle a POST request to load a previously generated configuration file.
    A user is only be able to load their own scenarios. User has to be logged in.

    :return: Redirect to the experimental environment, so it's a response.

    See also:
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    username: str = session.get('username', '').strip()
    selected_config_path: str = request.form.get('config_file')

    # Ensure and check if the selected configuration is within the user's directory
    user_directory: str = os.path.join(app.root_path, 'user', username)
    if not selected_config_path.startswith(user_directory):
        flash('Invalid configuration selected.')
        return redirect(url_for('experimental_environment'))

    # Load the config file
    try:
        with open(selected_config_path, 'r') as f:
            config_data: Any = json.load(f)
        # Store the config in the session or pass it to the template
        session['config_data'] = config_data
        return redirect(url_for('experimental_environment'))
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        flash('Error loading configuration.')
        return redirect(url_for('experimental_environment'))


@app.route('/delete_scenario', methods=['POST'])
@login_required
def delete_scenario() -> Response:
    """
    Delete a scenario configuration file. A user can only delete their own scenarios. User has to be logged in.

    :return: Redirect to the experimental environment, so it's a response.

    See also:
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    scenario_folder: Optional[str] = request.form.get('scenario_delete')
    scenario_folder: str = os.path.join(app.root_path, scenario_folder)

    if scenario_folder and os.path.exists(scenario_folder):
        try:
            # Delete the file
            shutil.rmtree(scenario_folder)
            flash(f"Configuration {scenario_folder} deleted successfully.", 'success')
        except Exception as e:
            flash(f"An error occurred while deleting the configuration: {str(e)}", 'error')
    else:
        flash(f"Selected configuration file {scenario_folder} does not exist.", 'error')

    return redirect(url_for('experimental_environment'))


@app.route('/receive_runtime_prediction', methods=['POST'])
def receive_runtime_prediction() -> (Response, int):
    """
    Receive a runtime prediction from the slurm cluster as a POST request and save the file.
    The user doesn't have to be logged in.

    :return: A response and an int providing the status.
    """
    user: Optional[str] = request.args.get('user')
    save_dir: str = os.path.join(app.root_path, 'user', user)

    data: Optional[Any] = request.get_json()

    if data:
        print(f"Received data from user: {user}")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data['timestamp'] = timestamp
        print(f"Timestamp added: {timestamp}")

        # Save JSON data to a file
        file_name = os.path.join(save_dir, f'{user}_runtime_prediction.json')
        with open(file_name, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        return jsonify({"status": "success", "user": user}), 200
    else:
        return jsonify({"status": "failed", "reason": "No JSON data received"}), 400


@app.route('/show_runtime_prediction')
@login_required
def show_runtime_prediction() -> (str, str, Optional[Any]):
    """
    Route to show the runtime prediction received from the Slurm cluster. User has to be logged in.

    :return: Render runtime prediction with user and data.

    See also:
        - [Login](../flask/app.html#login): Function to log in.
        - [Login required](../flask/app.html#login_required): Decorator to ensure login is required.
    """
    user: str = session.get('username')
    file_path: str = os.path.join(USER_DIR, user, f'{user}_runtime_prediction.json')

    if os.path.exists(file_path):
        # Load the file
        with open(file_path, 'r') as json_file:
            data: Any = json.load(json_file)
    else:
        data = None

    return render_template('runtime_prediction.html', user=user, data=data)


@app.route('/prepare-env', methods=['POST'])
@login_required
def prepare_env_route() -> Response:
    """
    Handle a POST request to prepare the environment for the user on the remote. User has to be logged in.

    :return: Redirect to the submit job route.

    See also:
        - [Login](../util/flask/app.html#login): Function to log in.
        - [Login required](../util/flask/app.html#login_required): Decorator to ensure login is required.
        - [prepare_env](../util/flask/environment.html#prepare_env): Function to prepare the environment for the user on the remote.
        - [setup_ssh_connection](../util/flask/ssh_setup.html#setup_ssh_connection): Function to set up the ssh connection and return an SSH client.
        - [transfer_experiments](../util/flask/environment.html#transfer_experiments): Function to transfer the simulation configuration files to the remote.
        - [create_db_key_on_remote](../util/flask/environment.html#create_db_key_on__remote): Function to send the database creation script to the remote.
    """
    try:
        prepare_env(session.get('username'))
        ssh_client = setup_ssh_connection(session.get('username'))
        transfer_experiments(ssh_client, os.path.join(USER_DIR, session.get('username')), session.get('username'))
        create_db_key_on_remote(ssh_client, os.path.abspath(os.path.join(app.root_path, '..', '..',
                                                                         "database")),
                                f"/home/{session.get('username')}")
        flash("Environment preparation started successfully.")
    except Exception as e:
        print(f"Error: {e}")
        flash(f"An error occurred: {e}")
    finally:
        ssh_client.close()

    # Redirect back to the new_job page after processing
    return redirect(url_for('submit_job'))


"""@app.route('/submit_job', methods=['GET', 'POST'])
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
        stdout, _ = execute_command(setup_ssh_connection(username),
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
                           num_compute_nodes=num_compute_nodes, json_files=json_files)"""


@app.route('/submit_job', methods=['GET', 'POST'])
@login_required
def submit_job() -> Any:
    """
    Handle the submission of jobs by users. On GET request, it displays the job submission page,
    including any existing JSON files and compute nodes. On POST request, it processes form data to either
    create a composite tree or start a simulation. User has to be logged in.

    :return: A rendered template or redirect response.

    See also:
        - [Login](../util/flask/app.html#login): Function to log in.
        - [Login required](../util/flask/app.html#login_required): Decorator to ensure login is required.
        - [setup_ssh_connection](../util/flask/ssh_setup.html#setup_ssh_connection): Set up SSH connection and returns it.
        - [get_jwt_token](../util/flask/app.html#get_jwt_token): Retrieve a JWT token from the slurm cluster.
        - [initialize_user_tree](../util/flask/app.html#initialize_user_tree): Initialize the user tree and returns it.
        - [find_json_files](../util/flask/app.html#find_json_files): Find all JSON configuration files associated with the user.
        - [get_num_compute_nodes](../util/flask/app.html#get_num_compute_nodes): Get the number of compute nodes available.
        - [get_user_accounts](../util/flask/app.html#get_user_accounts): Retrieve the list of all user accounts on the slurm.
        - [handle_create_tree](../util/flask/app.html#handle_create_tree): Handle the creation of a tree.
        - [handle_start_simulation](../util/flask/app.html#handle_start_simulation): Handle the start of simulations.
    """
    global user_trees
    username: str = session.get('username')
    ssh_client: SSHClient = setup_ssh_connection(username)
    jwt_token: str = get_jwt_token(ssh_client)

    user_directory: str = os.path.join(app.root_path, 'user', username)

    json_files: list[dict[str, str]] = find_json_files(user_directory)

    initialize_user_tree(username)

    try:
        num_compute_nodes: int = get_num_compute_nodes(username)

        accounts: list[str] = get_user_accounts(ssh_client, username)
        selected_account: Optional[str] = None

        if request.method == 'POST':

            if 'create_tree' in request.form:
                return handle_create_tree(username)

            elif 'start_simulation' in request.form:
                return handle_start_simulation(username, jwt_token)

    except Exception as e:
        logging.error(f"Error: {e}")
        flash(f"An error occurred while submitting job: {e}")

    return render_template('submit_job.html', accounts=accounts,
                           selected_account=selected_account, num_compute_nodes=num_compute_nodes,
                           json_files=json_files)


def get_jwt_token(ssh_client: SSHClient) -> str:
    """
    Obtain a JWT token from the slurm cluster using an SSH client.

    :param ssh_client : The SSH client connected to the remote server.

    :return: The JWT token as a string.

    See also:
        - [execute_command](../util/flask/environment.html#execute_command): Execute the command on the remote.
    """
    stdout, _ = execute_command(ssh_client, 'scontrol token lifespan=9999')
    # Parse the stdout to extract the token
    # stdout is structured as 'JWTToken=<token>'
    jwt_token: str = stdout.strip().split('=')[1]
    return jwt_token


def initialize_user_tree(username: str) -> None:
    """
    Initialize the user's composite tree if it doesn't exist.

    :param username: The username of the current user.
    """
    global user_trees
    if username not in user_trees:
        user_trees[username] = None  # No tree created


def get_num_compute_nodes(username: str) -> int:
    """
    Get the number of not running compute nodes in the user's composite tree.

    :param username: The username of the current user.

    :return: The number of compute nodes.

    See also:
        - [CompositeTree](../util/flask/composite_tree.html): Composite Pattern to submit jobs.
        - [count_not_running_compute_nodes](../util/flask/composite_tree.html#count_not_running_compute_nodes): Get the number of inactive compute nodes.
    """
    global user_trees
    num_compute_nodes: int = 0
    if user_trees[username] is not None:
        root = user_trees[username]
        num_compute_nodes = CompositeTree.count_not_running_compute_nodes(root)
    return num_compute_nodes


def get_user_accounts(ssh_client: SSHClient, username: str) -> list[str]:
    """
    Retrieve Slurm accounts for the given user via SSH.

    :param ssh_client: The SSH client connected to the remote server.
    :param username: The username of the current user.

    :return: A list of account names.

    See also:
        - [execute_command](../util/flask/environment.html#execute_command): Execute the command on the remote.
    """
    stdout, _ = execute_command(ssh_client, f"sacctmgr show assoc user={username} format=Account%30")
    lines = stdout.splitlines()
    accounts: list[str] = []
    if len(lines) > 2:
        accounts = [line.strip() for line in lines[2:] if line.strip()]
    return accounts


def handle_create_tree(username: str) -> Response:
    """
    Handle the creation of a composite tree for the user.

    :param username: The username of the current user.

    :return: A redirect response to the submit_job page.

    See also:
        - [CompositeTree](../util/flask/composite_tree.html): Composite Pattern to submit jobs.
        - [create_custom_composite_tree_with_params](../util/flask/composite_tree.html#create_custom_composite_tree_with_params): Create a custom composite tree.
    """
    num_children: int = int(request.form.get('num_children'))
    depth_of_tree: int = int(request.form.get('depth_of_tree'))

    user_trees[username] = CompositeTree.create_custom_composite_tree_with_params(num_children, depth_of_tree)

    flash("Composite Tree created successfully.")
    return redirect(url_for('submit_job'))


def handle_start_simulation(username: str, jwt_token: str) -> Any:
    """
    Handle starting the simulation.

    :param username: The username of the current user.
    :param jwt_token: The JWT token obtained via SSH.

    :return: A redirect response to the show_runtime_prediction page.

    See also:
        - [get_num_compute_nodes](../util/flask/app.html#get_num_compute_nodes): Get the number of inactive compute nodes.
        - [manipulate_scenario_path](../util/flask/environment.html#manipulate_scenario_path): Manipulate the scenario path.
        - [start_simulation_in_thread](../util/flask/app.html#start_simulation_in_thread): Start the simulation in a thread.
    """
    global user_trees

    if user_trees[username] is None:
        flash("Please create a Composite Tree first.")
        return redirect(url_for('submit_job'))

    # Check if the tree contains at least one compute node
    num_compute_nodes: int = get_num_compute_nodes(username)
    if num_compute_nodes < 1:
        flash("Your tree must contain at least one compute node to start the simulation.")
        return redirect(url_for('submit_job'))

    # Get simulation parameters
    selected_account: str = request.form.get('account')
    num_replications: int = int(request.form.get('num_replications'))
    num_compute_nodes: int = int(request.form.get('num_compute_nodes'))
    model_script: str = request.form.get('model_script')
    cpus_per_task: int = int(request.form.get('cpus_per_task'))  # New parameter cpus_per_task
    slurm_username: str = session.get('username')

    # Manipulate the model script path
    manipulated_model_script: str = manipulate_scenario_path(
        model_script,
        source_base_path=os.path.join(USER_DIR, username),
        destination_base_path_template=f'/cluster/user/{slurm_username}/DMPG_experiments'
    )

    time_limit = int(request.form.get('time_limit'))
    num_replications_per_node: int = round(num_replications / num_compute_nodes)

    # Start simulation in a separate thread
    simulation_thread = threading.Thread(
        target=start_simulation_in_thread,
        args=(
            username,
            num_replications_per_node,
            selected_account,
            slurm_username,
            model_script,
            manipulated_model_script,
            time_limit,
            jwt_token,
            cpus_per_task
        )
    )
    simulation_thread.start()

    flash("Simulation started successfully. All trees have been deleted.")
    return redirect(url_for('show_runtime_prediction'))


def start_simulation_in_thread(username: str, num_replications_per_node: int, selected_account: str,
                               slurm_username: str, model_script: str, manipulated_model_script: str,
                               time_limit: int, jwt_token: str, cpus_per_task: int) -> None:
    """
    Start the simulation in a separate thread.

    :param username: The username of the current user.
    :param num_replications_per_node: Number of replications per compute node.
    :param selected_account: The selected Slurm account.
    :param slurm_username: The Slurm username.
    :param model_script: The model script path.
    :param manipulated_model_script: The manipulated model script path.
    :param time_limit: The time limit for the simulation.
    :param jwt_token: The JWT token obtained via SSH.
    :param cpus_per_task: Number of CPUs per task for the simulation.

    See also:
        - [CompositeTree](../util/flask/composite_tree.html): Composite Pattern to submit jobs.
        - [distribute_and_compute](../util/flask/nodes_for_composite.html#distribute_and_compute):
    """
    global user_trees
    if user_trees.get(username) is not None:
        root = user_trees[username]
        print(root)

        # Include cpus_per_task in distribute_and_compute call
        root.distribute_and_compute(model=model_script, num_replications=num_replications_per_node,
                                    slurm_account=selected_account, model_script=manipulated_model_script,
                                    time_limit=time_limit, slurm_username=slurm_username,
                                    jwt_token=jwt_token, cpus_per_task=cpus_per_task)

        # After the simulation is completed, delete the user's tree only because of 2 jobs issue
        del user_trees[username]
        logging.info(f"All trees of the user {username} have been deleted.")
    else:
        logging.warning("No Composite Tree available for the simulation.")



def find_json_files(directory: str) -> list[dict[str, str]]:
    """
    Searches subdirectory for json files recursively.

    :param directory: The directory to search for json files.

    :return: A list of dictionaries containing the json filenames and the full path.
    """
    json_files: list[dict[str, str]] = []
    for root, dirs, files in os.walk(directory):
        # Skip root directory
        if root == directory:
            continue
        for file in files:
            if file.endswith('.json'):
                full_path: str = os.path.join(root, file)
                json_files.append({
                    'filename': file,
                    'full_path': full_path
                })

    return json_files


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
    logging.basicConfig(level=logging.DEBUG)
