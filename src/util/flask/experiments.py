import json
import os

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


import json
import logging

def generate_simulation_configuration(form_data, source_files):
    logging.info("Starting configuration generation")

    # Initialize the main configuration dictionary
    config = {
        'model_name': form_data.get('model_name'),
        'scenario_name': form_data.get('scenario_name'),
        'sources': [],
        'servers': [],
        'sinks': []
    }

    logging.info(f"Form data for model: {config['model_name']}, scenario: {config['scenario_name']}")

    # Process sources
    for key in form_data:
        if key.startswith('name_source_'):
            unique_id = key.replace('name_', '')  # Extract 'source_X' identifier
            logging.info(f"Processing source {unique_id}")
            source = {
                'name': form_data.get(f'name_{unique_id}'),
                'distribution': {
                    'type': form_data.get(f'dist_type_${unique_id}'),
                    'params': {}
                },
                'connections': [],
                'arrival_table': None
            }

            # Include CSV file path if available
            csv_file_path = source_files.get(unique_id)
            if csv_file_path:
                source['arrival_table'] = csv_file_path

            # Handle distribution parameters
            dist_type = form_data.get(f'dist_type_{unique_id}')
            if dist_type == 'triangular':
                source['distribution']['params'] = {
                    'low': float(form_data.get(f'low_{unique_id}', 0)),
                    'mode': float(form_data.get(f'mode_{unique_id}', 0)),
                    'high': float(form_data.get(f'high_{unique_id}', 0))
                }
            elif dist_type == 'uniform':
                source['distribution']['params'] = {
                    'low': float(form_data.get(f'low_{unique_id}', 0)),
                    'high': float(form_data.get(f'high_{unique_id}', 0))
                }
            elif dist_type == 'expovariate':
                source['distribution']['params'] = {
                    'lambda': float(form_data.get(f'lambda_{unique_id}', 0))
                }
            elif dist_type == 'normalvariate':
                source['distribution']['params'] = {
                    'mu': float(form_data.get(f'mu_{unique_id}', 0)),
                    'sigma': float(form_data.get(f'sigma_{unique_id}', 0))
                }

            # Process connections
            connection_number = 1
            while form_data.get(f'connection_{unique_id}_{connection_number}'):
                target_component = form_data.get(f'connection_{unique_id}_{connection_number}')
                probability = form_data.get(f'probability_{unique_id}_{connection_number}', '').strip()
                process_duration = form_data.get(f'process_duration_{unique_id}_{connection_number}', '').strip()

                # Convert probability and process_duration to float if they are provided
                probability = float(probability) if probability else None
                process_duration = float(process_duration) if process_duration else None

                connection = {
                    'target': target_component,
                    'probability': probability,
                    'process_duration': process_duration
                }

                source['connections'].append(connection)
                logging.info(f"Added connection to source {unique_id}: {connection}")
                connection_number += 1

            logging.info(f"Added source config: {source}")
            config['sources'].append(source)

    # Process servers
    for key in form_data:
        if key.startswith('name_server_'):
            unique_id = key.replace('name_', '')  # Extract 'server_X' identifier
            logging.info(f"Processing server {unique_id}")
            server = {
                'name': form_data.get(f'name_{unique_id}'),
                'distribution': {
                    'type': form_data.get(f'dist_type_{unique_id}'),
                    'params': {}
                },
                'queue_order': form_data.get(f'queue_order_{unique_id}'),
                'breakdown': {},
                'connections': []
            }

            # Handle distribution parameters
            dist_type = form_data.get(f'dist_type_{unique_id}')
            if dist_type == 'triangular':
                server['distribution']['params'] = {
                    'low': float(form_data.get(f'low_{unique_id}', 0)),
                    'mode': float(form_data.get(f'mode_{unique_id}', 0)),
                    'high': float(form_data.get(f'high_{unique_id}', 0))
                }
            elif dist_type == 'uniform':
                server['distribution']['params'] = {
                    'low': float(form_data.get(f'low_{unique_id}', 0)),
                    'high': float(form_data.get(f'high_{unique_id}', 0))
                }
            elif dist_type == 'expovariate':
                server['distribution']['params'] = {
                    'lambda': float(form_data.get(f'lambda_{unique_id}', 0))
                }
            elif dist_type == 'normalvariate':
                server['distribution']['params'] = {
                    'mu': float(form_data.get(f'mu_{unique_id}', 0)),
                    'sigma': float(form_data.get(f'sigma_{unique_id}', 0))
                }

            # Handle breakdown parameters
            time_between_breakdown = form_data.get(f'time_between_machine_breakdown_{unique_id}', '').strip()
            if time_between_breakdown:
                server['breakdown']['time_between_machine_breakdown'] = float(time_between_breakdown)
                breakdown_duration = form_data.get(f'machine_breakdown_duration_{unique_id}', '').strip()
                if breakdown_duration:
                    server['breakdown']['machine_breakdown_duration'] = float(breakdown_duration)

            # Process connections
            connection_number = 1
            while form_data.get(f'connection_{unique_id}_{connection_number}'):
                target_component = form_data.get(f'connection_{unique_id}_{connection_number}')
                probability = form_data.get(f'probability_{unique_id}_{connection_number}', '').strip()
                process_duration = form_data.get(f'process_duration_{unique_id}_{connection_number}', '').strip()

                probability = float(probability) if probability else None
                process_duration = float(process_duration) if process_duration else None

                connection = {
                    'target': target_component,
                    'probability': probability,
                    'process_duration': process_duration
                }

                server['connections'].append(connection)
                logging.info(f"Added connection to server {unique_id}: {connection}")
                connection_number += 1

            logging.info(f"Added server config: {server}")
            config['servers'].append(server)

    # Process sinks
    for key in form_data:
        if key.startswith('name_sink_'):
            unique_id = key.replace('name_', '')  # Extract 'sink_X' identifier
            logging.info(f"Processing sink {unique_id}")
            sink = {
                'name': form_data.get(f'name_{unique_id}'),
                'addon_process_trigger': form_data.get(f'addon_process_trigger_{unique_id}')
            }
            config['sinks'].append(sink)
            logging.info(f"Added sink config: {sink}")

    config_json = json.dumps(config, indent=4)
    logging.info(f"Generated config: {config_json}")
    return config_json


def save_config_file(config_json, path, filename):
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, filename)

    with open(file_path, 'w') as f:
        f.write(config_json)


def save_arrival_table(arrival_table_file, model_name, scenario_name, source_name, username):
    # Create the directory structure based on user/model/scenario
    base_directory = os.path.join('user', username, model_name, scenario_name, 'arrival_tables')
    os.makedirs(base_directory, exist_ok=True)

    # Generate a secure filename and prepend the source name
    filename = secure_filename(arrival_table_file.filename)
    filename_with_source = f"{source_name}_{filename}"

    # Save the file to the directory
    file_path = os.path.join(base_directory, filename_with_source)
    arrival_table_file.save(file_path)

    # Return the file path for inclusion in the configuration
    return file_path


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
