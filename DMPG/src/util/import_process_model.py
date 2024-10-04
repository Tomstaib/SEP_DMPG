from src.core.source import Source
from src.core.server import Server
from src.core.sink import Sink
import pandas as pd
import xml.etree.ElementTree as ET
import random


def import_model(env, filepath='config.xml'):
    # Parse the XML configuration file
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Extract relevant information from the XML configuration
    components = {}

    # Iterate over all <component> elements in the configuration
    for component_elem in root.findall('components/component'):
        component_type = component_elem.find('type').text
        component_name = component_elem.find('name').text

        if component_type == 'Source':
            # Extract the arrival table for each source
            arrival_table_data = component_elem.find('arrival_table')   # [int(value) for value in component_elem.find('arrival_table').text.split(',')]
            if arrival_table_data:
                arrival_table = [int(value) for value in arrival_table_data.text.split(',')]
                arrival_table = pd.DataFrame(arrival_table, columns=['arrival time'])
                component = Source(env, component_name, arrival_table=arrival_table)
            else:
                creation_time_distribution = tuple(component_elem.find('creation_time_distribution').text.split(','))
                # creation_time_distribution = (creation_time_distribution[0], int(creation_time_distribution[1]))
                creation_time_distribution = import_distribution_function(creation_time_distribution)
                component = Source(env, component_name, creation_time_distribution_with_parameters=creation_time_distribution)
        elif component_type == 'Server':
            component_params = tuple(component_elem.find('params').text.split(','))
            # component_params = (component_params[0], int(component_params[1]))
            component_params = import_distribution_function(component_params)
            component = Server(env, component_name, component_params)
        elif component_type == 'Sink':
            component = Sink(env, component_name)
        else:
            raise ValueError(f"Unknown component type: {component_type}")

        components[component_name] = component

    # Connect the components based on the configuration
    for connection_elem in root.findall('connections/connection'):
        source_name = connection_elem.find('source').text
        target_name = connection_elem.find('target').text

        source_component = components.get(source_name)
        target_component = components.get(target_name)

        if source_component is None or target_component is None:
            raise ValueError(f"Invalid connection: {source_name} to {target_name}")

        source_component.connect(target_component)


def import_distribution_function(distribution_text):
    # distribution = distribution_text[0]
    # params = distribution_text[1]
    # if distribution == "exponential":
    return lambda: (random.triangular, 1, 2, 3)


def modify_arrival_table(xml_file_path, source_name, new_arrival_table):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Find the source component with the specified name and update its arrival_table
    for component_elem in root.findall('.//component'):
        type_elem = component_elem.find('type')
        name_elem = component_elem.find('name')
        arrival_table_elem = component_elem.find('arrival_table')

        if type_elem is not None and type_elem.text == 'Source' and name_elem is not None and name_elem.text == source_name:
            # Modify the arrival_table content
            arrival_table_elem.text = new_arrival_table

    # Save the modified XML back to the file
    tree.write(xml_file_path)


def modify_creation_time_distribution(xml_file_path, source_name, new_distribution):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Find the source component with the specified name and update its creation_time_distribution
    for component_elem in root.findall('.//component'):
        type_elem = component_elem.find('type')
        name_elem = component_elem.find('name')
        creation_time_elem = component_elem.find('creation_time_distribution')

        if type_elem is not None and type_elem.text == 'Source' and name_elem is not None and name_elem.text == source_name:
            # Modify the creation_time_distribution content
            creation_time_elem.text = new_distribution

    # Save the modified XML back to the file
    tree.write(xml_file_path)
