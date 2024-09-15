import json
import os

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



def generate_config(form_data, username):
    """Generates the configuration JSON file based on form data and saves it to a file."""

    # Collect model and scenario names
    model_name = form_data.get('model_name', 'model_1')
    scenario_name = form_data.get('scenario_name', 'scenario_1')

    # Sources
    sources = []
    for i in range(1, len([key for key in form_data.keys() if key.startswith('source_name_')]) + 1):
        source_name = form_data[f'source_name_{i}']
        entity_creation_rate = float(form_data[f'entity_creation_rate_{i}'])
        sources.append({
            "name": source_name,
            "entity_creation_rate": entity_creation_rate
        })

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

    return config_filename
