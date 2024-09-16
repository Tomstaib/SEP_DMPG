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

def generate_simulation_configuration(form_data):
    logging.info("Starting configuration generation")

    # Initialize the main configuration dictionary
    config = {
        'model_name': form_data.get('model_name'),
        'scenario_name': form_data.get('scenario_name'),
        'sources': [],
        'servers': [],
        'sinks': []
    }

    logging.warning(f"Form data for model: {form_data.get('model_name')}, scenario: {form_data.get('scenario_name')}")

    # Process sources
    source_count = 1
    while form_data.get(f'source_name_{source_count}'):
        logging.warning(f"Processing source {source_count}")
        source = {
            'name': form_data.get(f'source_name_{source_count}'),
            'distribution': {
                'type': form_data.get(f'dist_type_{source_count}'),
                'params': {}
            }
        }

        dist_type = form_data.get(f'dist_type_{source_count}')
        if dist_type == 'triangular':
            source['distribution']['params'] = {
                'low': float(form_data.get(f'low_{source_count}', 0)),
                'mode': float(form_data.get(f'mode_{source_count}', 0)),
                'high': float(form_data.get(f'high_{source_count}', 0))
            }
        elif dist_type == 'uniform':
            source['distribution']['params'] = {
                'low': float(form_data.get(f'low_{source_count}', 0)),
                'high': float(form_data.get(f'high_{source_count}', 0))
            }
        elif dist_type == 'expovariate':
            source['distribution']['params'] = {
                'lambda': float(form_data.get(f'lambda_{source_count}', 0))
            }
        elif dist_type == 'normalvariate':
            source['distribution']['params'] = {
                'mu': float(form_data.get(f'mu_{source_count}', 0)),
                'sigma': float(form_data.get(f'sigma_{source_count}', 0))
            }

        logging.info(f"Added source config: {source}")
        config['sources'].append(source)
        source_count += 1

    # Process servers
    server_count = 1
    while form_data.get(f'server_name_{server_count}'):
        logging.info(f"Processing server {server_count}")
        server = {
            'name': form_data.get(f'server_name_{server_count}'),
            'distribution': {
                'type': form_data.get(f'dist_type_{server_count}'),
                'params': {}
            },
            'queue_order': form_data.get(f'queue_order_{server_count}'),
            'breakdown': {
                'time_between_machine_breakdown': form_data.get(f'time_between_machine_breakdown_{server_count}'),
                'machine_breakdown_duration': form_data.get(f'machine_breakdown_duration_{server_count}')
            }
        }

        dist_type = form_data.get(f'dist_type_{server_count}')
        if dist_type == 'triangular':
            server['distribution']['params'] = {
                'low': float(form_data.get(f'low_{server_count}', 0)),
                'mode': float(form_data.get(f'mode_{server_count}', 0)),
                'high': float(form_data.get(f'high_{server_count}', 0))
            }
        elif dist_type == 'uniform':
            server['distribution']['params'] = {
                'low': float(form_data.get(f'low_{server_count}', 0)),
                'high': float(form_data.get(f'high_{server_count}', 0))
            }
        elif dist_type == 'expovariate':
            server['distribution']['params'] = {
                'lambda': float(form_data.get(f'lambda_{server_count}', 0))
            }
        elif dist_type == 'normalvariate':
            server['distribution']['params'] = {
                'mu': float(form_data.get(f'mu_{server_count}', 0)),
                'sigma': float(form_data.get(f'sigma_{server_count}', 0))
            }

        logging.info(f"Added server config: {server}")
        config['servers'].append(server)
        server_count += 1

    # Process sinks
    sink_count = 1
    while form_data.get(f'sink_name_{sink_count}'):
        logging.info(f"Processing sink {sink_count}")
        sink = {
            'name': form_data.get(f'sink_name_{sink_count}'),
            'addon_process_trigger': form_data.get(f'addon_process_trigger_{sink_count}')
        }
        config['sinks'].append(sink)
        sink_count += 1

    config_json = json.dumps(config, indent=4)
    logging.warning(f"Generated config: {config_json}")
    return config_json


def save_config_file(config_json, path, filename):
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, filename)

    with open(file_path, 'w') as f:
        f.write(config_json)


def save_arrival_table(arrival_table_file, model_name, scenario_name, source_files, source_name, username):
    # Create the directory structure based on user/model/scenario
    base_directory = os.path.join('user', username, model_name, scenario_name, 'arrival_tables', )
    os.makedirs(base_directory, exist_ok=True)
    # Generate a secure filename and prepend the source name
    filename = secure_filename(arrival_table_file.filename)
    filename_with_source = f"{source_name}_{filename}"
    # Save the file to the directory
    file_path = os.path.join(base_directory, filename_with_source)
    arrival_table_file.save(file_path)
    logging.info(f"File for {source_name} uploaded successfully: {file_path}")
    # Store the file path in the dictionary for later use in config generation
    source_files[source_name] = file_path


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
