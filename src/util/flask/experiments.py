import os
import shutil
import json
from typing import Any

from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.utils import secure_filename


def generate_simulation_configuration(form_data, source_files: dict[str, str]) -> str:
    """
    Generate a simulation configuration file from the form data provided in the html.

    :param form_data: The form data provided in the html form.
    :param source_files: A dictionary mapping the component IDs to the arrival tables.

    :return: The simulation configuration file as a string.
    """
    config: dict = {'model_name': form_data.get('model_name', '').strip(),
                    'scenario_name': form_data.get('scenario_name', '').strip(),
                    'minutes': form_data.get('simulation_minutes', 1),
                    'sources': process_sources(form_data, source_files),
                    'servers': process_servers(form_data), 'sinks': process_sinks(form_data)}

    return json.dumps(config, indent=4)


def process_sources(form_data, source_files: dict[str, str]) \
        -> list[dict[str, None | dict[str, dict] | list | list[dict[str, Any]]]]:
    """
    Process the sources provided in the form data provided in the html form with their corresponding arrival tables.

    :param form_data: The form data provided in the html form.
    :param source_files: A dictionary mapping the component IDs to the arrival tables.

    :return: A list containing all sources.

    See also:
        - [Source](../core/source.html)
        - [get_distribution_params](../util/flask/experiments.html#get_distribution_params)
        - [process_connections](../util/flask/experiments.html#process_connections)
    """
    sources: list[dict[str, None | dict[str, dict] | list | list[dict[str, Any]]]] = []
    for key in form_data:
        if key.startswith('name_source_'):
            unique_id = key.replace('name_', '')  # Extract 'source_X' identifier
            source = {
                'id': unique_id,
                'name': form_data.get(f'name_{unique_id}'),
                'distribution': {
                    'type': form_data.get(f'dist_type_{unique_id}'),
                    'params': {}
                },
                'connections': [],
                'arrival_table': None
            }

            arrival_table_path: str = source_files.get(unique_id)
            if arrival_table_path:
                source['arrival_table'] = arrival_table_path

            # Populate distribution parameters
            source['distribution']['params'] = get_distribution_params(form_data, unique_id,
                                                                       source['distribution']['type'])

            # Process connections
            source['connections'] = process_connections(form_data, unique_id)

            sources.append(source)

    return sources


def process_servers(form_data) -> list:
    """
    Process the servers provided in the form data provided in the html form.

    :param form_data: The form data provided in the html form.

    :return: A list containing all servers.

    See also:
        - [Server](../core/server.html)
        - [get_distribution_params](../util/flask/experiments.html#get_distribution_params)
        - [get_breakdown_params](../util/flask/experiments.html#get_breakdown_params)
        - [process_connections](../util/flask/experiments.html#process_connections)
    """
    servers: list = []
    for key in form_data:
        if key.startswith('name_server_'):
            unique_id = key.replace('name_', '')  # Extract 'server_X' identifier
            server = {
                'id': unique_id,
                'name': form_data.get(f'name_{unique_id}'),
                'distribution': {
                    'type': form_data.get(f'dist_type_{unique_id}'),
                    'params': {}
                },
                'queue_order': form_data.get(f'queue_order_{unique_id}', 'FIFO'),
                'breakdown': {},
                'connections': []
            }

            server['distribution']['params'] = get_distribution_params(form_data, unique_id,
                                                                       server['distribution']['type'])

            server['breakdown'] = get_breakdown_params(form_data, unique_id)

            server['connections'] = process_connections(form_data, unique_id)

            servers.append(server)

    return servers


def process_sinks(form_data) -> list[dict[str, Any]]:
    """
    Process the sinks provided in the form data provided in the html form.

    :param form_data: The form data provided in the html form.

    :return: A list containing all sinks.

    See also:
        - [Sink](../core/sink.html)
    """
    sinks: list[dict[str, Any]] = []
    for key in form_data:
        if key.startswith('name_sink_'):
            unique_id = key.replace('name_', '')  # Extract 'sink_X' identifier
            sink = {
                'id': unique_id,  # Include the unique ID
                'name': form_data.get(f'name_{unique_id}'),
                'addon_process_trigger': form_data.get(f'addon_process_trigger_{unique_id}', ''),
            }
            sinks.append(sink)

    return sinks


def get_distribution_params(form_data, unique_id: str, dist_type: str) -> dict[str, Any]:
    """
    Retrieve the distribution parameters for a specific component.

    :param form_data: The form data provided in the html form.
    :param unique_id: The unique ID of the component.
    :param dist_type: The type of distribution.

    :return: The distribution parameters.

    See also:
        - [get_value_from_distribution_with_parameters](../util/helper.html#get_value_from_distribution_with_parameters)
    """
    params: dict[str, Any] = {}

    if dist_type == 'triangular':
        params['low'] = form_data.get(f'low_{unique_id}')
        params['mode'] = form_data.get(f'mode_{unique_id}')
        params['high'] = form_data.get(f'high_{unique_id}')

    elif dist_type == 'uniform':
        params['low'] = form_data.get(f'low_{unique_id}')
        params['high'] = form_data.get(f'high_{unique_id}')

    elif dist_type == 'expovariate':
        params['lambda'] = form_data.get(f'lambda_{unique_id}')

    elif dist_type == 'normalvariate':
        params['mu'] = form_data.get(f'mu_{unique_id}')
        params['sigma'] = form_data.get(f'sigma_{unique_id}')

    return params


def get_breakdown_params(form_data, unique_id: str) -> dict:
    """
    Get the breakdown parameters from the form data for a specific component.

    :param form_data: The form data provided in the html form.
    :param unique_id: The unique ID of the component.
    """
    breakdown: dict = {}

    # Time Between Machine Breakdown
    breakdown_dist_type = form_data.get(f'breakdown_dist_type_{unique_id}')
    if breakdown_dist_type:
        breakdown['time_between_machine_breakdown'] = {
            'type': breakdown_dist_type,
            'params': get_breakdown_distribution_params(form_data, unique_id, 'breakdown_')
        }

    # Machine Breakdown Duration
    breakdown_duration_dist_type = form_data.get(f'breakdown_duration_dist_type_{unique_id}')
    if breakdown_duration_dist_type:
        breakdown['machine_breakdown_duration'] = {
            'type': breakdown_duration_dist_type,
            'params': get_breakdown_distribution_params(form_data, unique_id, 'breakdown_duration_')
        }

    return breakdown


def get_breakdown_distribution_params(form_data, unique_id: str, prefix: str) -> dict[str, Any]:
    """
    Get the breakdown parameters from the form data for a specific component.

    :param form_data: The form data provided in the html form.
    :param unique_id: The unique ID of the component.
    :param prefix: The prefix of the breakdown parameter.

    :return: The breakdown parameters in a dictionary.
    """
    params: dict[str, Any] = {}
    if prefix == 'breakdown_':
        params['low'] = form_data.get(f'breakdown_low_{unique_id}')
        params['mode'] = form_data.get(f'breakdown_mode_{unique_id}')
        params['high'] = form_data.get(f'breakdown_high_{unique_id}')

    elif prefix == 'breakdown_duration_':
        params['low'] = form_data.get(f'breakdown_duration_low_{unique_id}')
        params['mode'] = form_data.get(f'breakdown_duration_mode_{unique_id}')
        params['high'] = form_data.get(f'breakdown_duration_high_{unique_id}')

    return params


def process_connections(form_data, unique_id: str) -> list[dict[str, Any]]:
    """
    Process the connections between components based on the form data.

    :param form_data: The form data provided in the html form.
    :param unique_id: The unique ID of the component.

    :return: The connections between components based on the form data in a dictionary.

    See also:
        - [Connections](../core/connections.html)
    """
    connections: list[dict[str, Any]] = []
    connection_index: int = 1
    while True:
        connection_key: str = f'connection_{unique_id}_{connection_index}'
        target = form_data.get(connection_key)
        if not target:
            break

        connection: dict[str, Any] = {
            'target': target,
            'probability': form_data.get(f'probability_{unique_id}_{connection_index}'),
            'process_duration': form_data.get(f'process_duration_{unique_id}_{connection_index}')
        }
        connections.append(connection)
        connection_index += 1

    return connections


def save_config_file(config_json: str, path: str, filename: str):
    """
    Save the configuration file to a file.

    :param config_json: The configuration file as a string.
    :param path: The path where the configuration file should be saved.
    :param filename: The name of the configuration file.
    """
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, filename)

    with open(file_path, 'w') as f:
        f.write(config_json)


def save_arrival_table(arrival_table_file: FileStorage, model_name: str, scenario_name: str,
                       source_name: str, user_directory: str, username: str) -> str:
    """
    Save the arrival table to a file.

    :param arrival_table_file: The arrival table as a file.
    :param model_name: The name of the model.
    :param scenario_name: The name of the scenario.
    :param user_directory: The user directory on the server.
    :param source_name: The name of the source corresponding to the arrival table.
    :param username: The name of the user who wants to save the arrival table.

    :return: The path to the saved arrival table.
    """

    filename: str = secure_filename(arrival_table_file.filename)
    filename_without_ext, _ = os.path.splitext(filename)
    filename_without_ext_normalized = secure_filename(filename_without_ext)

    filename_with_source = check_filename(filename, filename_without_ext_normalized, source_name)

    base_directory: str = os.path.join(user_directory, username, model_name, scenario_name, 'arrival_tables')
    os.makedirs(base_directory, exist_ok=True)
    file_path: str = os.path.join(base_directory, filename_with_source)

    arrival_table_file.save(file_path)

    return file_path


def copy_arrival_table(existing_file_path: str, new_model_name: str, new_scenario_name: str,
                       source_name: str, username: str) -> str:
    """
    Copy an arrival table to another scenario.

    :param existing_file_path: The path to the existing arrival table.
    :param new_model_name: The name of the new model.
    :param new_scenario_name: The name of the new scenario.
    :param source_name: The name of the source corresponding to the arrival table.
    :param username: The name of the user who wants to save the arrival table.

    :return: The path to the saved arrival table.
    """
    user_directory: str = os.path.abspath(os.path.join('user', username))
    existing_file_path_abs: str = os.path.abspath(existing_file_path)
    if not existing_file_path_abs.startswith(user_directory):
        raise ValueError("Invalid existing arrival table path.")

    # Construct new directory path
    base_directory: str = os.path.join('user', username, new_model_name, new_scenario_name, 'arrival_tables')
    os.makedirs(base_directory, exist_ok=True)

    # Get the filename from existing file path
    filename: str = os.path.basename(existing_file_path)
    filename_without_ext, _ = os.path.splitext(filename)
    filename_without_ext_normalized: str = secure_filename(filename_without_ext)

    filename_with_source: str = check_filename(filename, filename_without_ext_normalized, source_name)

    new_file_path = os.path.join(base_directory, filename_with_source)

    shutil.copyfile(existing_file_path, new_file_path)

    return new_file_path


def check_filename(filename: str, filename_without_ext_normalized: str, source_name: str) -> str:
    """
    Check the filename for the source name and add it if necessary.

    :param filename: The name of the file.
    :param filename_without_ext_normalized: The name of the file without extension.
    :param source_name: The name of the source corresponding to the arrival table.

    :return: The new path to the saved arrival table.
    """
    normalized_source_name = secure_filename(source_name)
    # Check if source_name is already in the filename
    if not filename_without_ext_normalized.startswith(normalized_source_name):
        # Prepend source_name to the filename
        filename_with_source: str = f"{normalized_source_name}_{filename}"
    else:
        # Use the original filename
        filename_with_source: str = filename

    return filename_with_source
