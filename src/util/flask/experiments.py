import json
import os
import shutil
import json
from werkzeug.utils import secure_filename

SAVE_DIR = r'E:\projects\SEP_DMPG\src\util\flask\received_data'


def load_runtime_prediction():
    """Loads the runtime prediction from a JSON file."""
    file_name = os.path.join(SAVE_DIR, 'runtime_prediction.json')

    if os.path.exists(file_name):
        with open(file_name, 'r') as json_file:
            data = json.load(json_file)
    else:
        data = {}  # Return an empty dictionary if the file doesn't exist
    return data


def save_runtime_prediction(data):
    """Saves the runtime prediction to a JSON file."""
    file_name = os.path.join(SAVE_DIR, 'runtime_prediction.json')

    with open(file_name, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def generate_simulation_configuration(form_data, source_files):
    # Initialize the base configuration dictionary
    config = {
        'model_name': form_data.get('model_name', '').strip(),
        'scenario_name': form_data.get('scenario_name', '').strip(),
        'sources': [],
        'servers': [],
        'sinks': []
    }

    # Process sources, servers, and sinks using modular functions
    config['sources'] = process_sources(form_data, source_files)
    config['servers'] = process_servers(form_data)
    config['sinks'] = process_sinks(form_data)

    return json.dumps(config, indent=4)

# Helper function to process sources
def process_sources(form_data, source_files):
    sources = []
    for key in form_data:
        if key.startswith('name_source_'):
            unique_id = key.replace('name_', '')  # Extract 'source_X' identifier
            source = {
                'id': unique_id,  # Include the unique ID
                'name': form_data.get(f'name_{unique_id}'),
                'distribution': {
                    'type': form_data.get(f'dist_type_{unique_id}'),
                    'params': {}
                },
                'connections': [],
                'arrival_table': None
            }

            # Include arrival table path if available
            arrival_table_path = source_files.get(unique_id)
            if arrival_table_path:
                source['arrival_table'] = arrival_table_path

            # Populate distribution parameters
            source['distribution']['params'] = get_distribution_params(form_data, unique_id, source['distribution']['type'])

            # Process connections
            source['connections'] = process_connections(form_data, unique_id)

            sources.append(source)
    return sources

# Helper function to process servers
def process_servers(form_data):
    servers = []
    for key in form_data:
        if key.startswith('name_server_'):
            unique_id = key.replace('name_', '')  # Extract 'server_X' identifier
            server = {
                'id': unique_id,  # Include the unique ID
                'name': form_data.get(f'name_{unique_id}'),
                'distribution': {
                    'type': form_data.get(f'dist_type_{unique_id}'),
                    'params': {}
                },
                'queue_order': form_data.get(f'queue_order_{unique_id}', 'FIFO'),
                'breakdown': {},
                'connections': []
            }

            # Populate distribution parameters for processing time
            server['distribution']['params'] = get_distribution_params(form_data, unique_id, server['distribution']['type'])

            # Populate breakdown parameters
            server['breakdown'] = get_breakdown_params(form_data, unique_id)

            # Process connections
            server['connections'] = process_connections(form_data, unique_id)

            servers.append(server)
    return servers

# Helper function to process sinks
def process_sinks(form_data):
    sinks = []
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

# Helper function to get distribution parameters based on type
def get_distribution_params(form_data, unique_id, dist_type):
    params = {}
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

# Helper function to get breakdown parameters
def get_breakdown_params(form_data, unique_id):
    breakdown = {}

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

# Helper function to get breakdown distribution parameters
def get_breakdown_distribution_params(form_data, unique_id, prefix):
    params = {}
    if prefix == 'breakdown_':
        params['low'] = form_data.get(f'breakdown_low_{unique_id}')
        params['mode'] = form_data.get(f'breakdown_mode_{unique_id}')
        params['high'] = form_data.get(f'breakdown_high_{unique_id}')
    elif prefix == 'breakdown_duration_':
        params['low'] = form_data.get(f'breakdown_duration_low_{unique_id}')
        params['mode'] = form_data.get(f'breakdown_duration_mode_{unique_id}')
        params['high'] = form_data.get(f'breakdown_duration_high_{unique_id}')
    return params

# Helper function to process connections
def process_connections(form_data, unique_id):
    connections = []
    connection_index = 1
    while True:
        connection_key = f'connection_{unique_id}_{connection_index}'
        target = form_data.get(connection_key)
        if not target:
            break
        connection = {
            'target': target,
            'probability': form_data.get(f'probability_{unique_id}_{connection_index}'),
            'process_duration': form_data.get(f'process_duration_{unique_id}_{connection_index}')
        }
        connections.append(connection)
        connection_index += 1
    return connections




def save_config_file(config_json, path, filename):
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, filename)

    with open(file_path, 'w') as f:
        f.write(config_json)


def save_arrival_table(arrival_table_file, model_name, scenario_name, source_name, username):
    # Secure the filename to prevent directory traversal attacks
    filename = secure_filename(arrival_table_file.filename)
    filename_without_ext, ext = os.path.splitext(filename)
    filename_without_ext_normalized = secure_filename(filename_without_ext)

    # Normalize source_name to be comparable to filename_without_ext
    normalized_source_name = secure_filename(source_name)

    # Check if source_name is already in the filename
    if not filename_without_ext_normalized.startswith(normalized_source_name):
        # Prepend source_name to the filename
        filename_with_source = f"{normalized_source_name}_{filename}"
    else:
        # Use the original filename
        filename_with_source = filename

    # Define the path to save the arrival table
    base_directory = os.path.join('user', username, model_name, scenario_name, 'arrival_tables')
    os.makedirs(base_directory, exist_ok=True)
    file_path = os.path.join(base_directory, filename_with_source)

    # Save the arrival table file
    arrival_table_file.save(file_path)

    # Return the file path
    return file_path


def copy_arrival_table(existing_file_path, new_model_name, new_scenario_name, source_name, username):
    # Validate existing_file_path
    user_directory = os.path.abspath(os.path.join('user', username))
    existing_file_path_abs = os.path.abspath(existing_file_path)
    if not existing_file_path_abs.startswith(user_directory):
        raise ValueError("Invalid existing arrival table path.")

    # Construct the new directory path
    base_directory = os.path.join('user', username, new_model_name, new_scenario_name, 'arrival_tables')
    os.makedirs(base_directory, exist_ok=True)

    # Get the filename from the existing file path
    filename = os.path.basename(existing_file_path)
    filename_without_ext, ext = os.path.splitext(filename)
    filename_without_ext_normalized = secure_filename(filename_without_ext)

    # Normalize source_name to be comparable to filename_without_ext
    normalized_source_name = secure_filename(source_name)

    # Check if source_name is already in the filename
    if not filename_without_ext_normalized.startswith(normalized_source_name):
        # Prepend source_name to the filename
        filename_with_source = f"{normalized_source_name}_{filename}"
    else:
        # Use the original filename
        filename_with_source = filename

    # Construct the new file path
    new_file_path = os.path.join(base_directory, filename_with_source)

    # Copy the file
    shutil.copyfile(existing_file_path, new_file_path)

    # Return the new file path
    return new_file_path

"""def generate_config(form_data, username, source_files):

    # Collect model and scenario names
    model_name = form_data.get('model_name', 'model_1')
    scenario_name = form_data.get('scenario_name', 'scenario_1')

    # Iterate through the sources in the form
    for key in form_data:
        if key.startswith('source_name_'):
            source_index = key.split('_')[-1]
            source_name = form_data[key].strip()

            # Get the uploaded file path for the source
            file_path = source_files.get(source_name)

            # Create the source configuration
            source_config = {
                'name': source_name,
                'creation_rate': form_data.get(f'entity_creation_rate_{source_index}'),
                'distribution': form_data.get(f'dist_type_{source_index}'),
                'file_path': file_path  # Add the file path to the config
            }

            config['sources'].append(source_config)

    # Servers
    servers = []
    for i in range(1, len([key for key in form_data.keys() if key.startswith('server_name_')]) + 1):
        server_name = form_data[f'server_name_{i}']
        dist_type = form_data[f'server_dist_{i}']
        low = float(form_data[f'low_{i}'])
        high = float(form_data[f'high_{i}'])
        servers.append({
            "name": server_name,
            "time_distribution": {
                "distribution": dist_type,
                "low": low,
                "high": high
            }
        })

    # Collecting sinks
    sinks = []
    sink_count = len([key for key in form_data.keys() if key.startswith('sink_name_')])
    for i in range(1, sink_count + 1):
        sink_name = form_data[f'sink_name_{i}']
        sinks.append({"name": sink_name})

    # Collecting combiners
    combiners = []
    combiner_count = len([key for key in form_data.keys() if key.startswith('combiner_name_')])
    for i in range(1, combiner_count + 1):
        combiner_name = form_data[f'combiner_name_{i}']
        combiners.append({"name": combiner_name})

    # Collecting separators
    separators = []
    separator_count = len([key for key in form_data.keys() if key.startswith('separator_name_')])
    for i in range(1, separator_count + 1):
        separator_name = form_data[f'separator_name_{i}']
        separators.append({"name": separator_name})

    # Create the final config
    config = {
        "model_name": model_name,
        "scenario_name": scenario_name,
        "sources": sources,
        "servers": servers,
        "sinks": sinks,
        "combiners": combiners,
        "separators": separators
    }

    # Save the config to a JSON file
    config_filename = os.path.join(SAVE_DIR, f'{username}_config.json')
    with open(config_filename, 'w') as f:
        json.dump(config, f, indent=4)

    return config_filename"""
