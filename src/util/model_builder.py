import json
import os
import random

from core.server import Server
from core.sink import Sink
from core.source import Source
from util.simulations import run_simulation
from util.visualization import visualize_system


def build_model_from_config(config_path):
    def model_function(env):
        # Load the configuration file
        with open(config_path, 'r') as f:
            config = json.load(f)

        components = {}  # Dictionary to hold all components by unique ID

        flask_base_path = os.path.abspath(os.path.join(os.path.dirname(config_path), '../flask'))

        # Function to get component unique ID
        def get_component_id(component_config):
            return component_config.get('id', component_config['name'])

        # Create sources
        for source_config in config.get('sources', []):
            name = source_config['name']
            component_id = source_config['id']
            distribution = source_config['distribution']
            arrival_table_path = source_config.get('arrival_table')

            # Only prepend the base path if the path is not absolute and does not already contain a valid reference
            if arrival_table_path and not os.path.isabs(arrival_table_path) and not arrival_table_path.startswith(
                    "user"):
                arrival_table_path = os.path.join(flask_base_path, arrival_table_path)

            # Determine interarrival time distribution
            interarrival_time_dist = get_distribution(distribution) if distribution[
                                                                           'type'] != 'arrival_table' else None

            source = Source(env, name, creation_time_distribution_with_parameters=interarrival_time_dist,
                            arrival_table_path=arrival_table_path)
            components[component_id] = source

        # Create servers
        for server_config in config.get('servers', []):
            unique_id = get_component_id(server_config)
            name = server_config['name']
            distribution = server_config.get('distribution', {})
            processing_time_dist = get_distribution(distribution) if distribution else None

            # Breakdown parameters
            breakdown_config = server_config.get('breakdown', {})
            breakdown_time_dist = get_distribution(
                breakdown_config.get('time_between_machine_breakdown')
            ) if breakdown_config.get('time_between_machine_breakdown') else None
            breakdown_duration_dist = get_distribution(
                breakdown_config.get('machine_breakdown_duration')
            ) if breakdown_config.get('machine_breakdown_duration') else None

            queue_order = server_config.get('queue_order', 'FIFO')

            server = Server(
                env,
                name,
                processing_time_distribution_with_parameters=processing_time_dist,
                time_between_machine_breakdowns=breakdown_time_dist,
                machine_breakdown_duration=breakdown_duration_dist,
                queue_order=queue_order
            )
            components[unique_id] = server

        # Create sinks
        for sink_config in config.get('sinks', []):
            unique_id = get_component_id(sink_config)
            name = sink_config['name']
            addon_process_trigger = sink_config.get('addon_process_trigger', None)
            sink = Sink(env, name, addon_process_trigger=addon_process_trigger)
            components[unique_id] = sink

        # Set up connections
        for component_config in config.get('sources', []) + config.get('servers', []):
            component_id = get_component_id(component_config)
            # print(component_id)
            component = components[component_id]
            for connection in component_config.get('connections', []):
                target_id = connection['target']
                target_component = components.get(target_id)
                if not target_component:
                    raise ValueError(f"Target component '{target_id}' not found for connection.")

                probability = connection.get('probability')
                if probability:
                    probability = float(probability)
                else:
                    probability = None

                process_duration = connection.get('process_duration')
                if process_duration:
                    process_duration = float(process_duration)
                else:
                    process_duration = None

                component.connect(
                    target_component,
                    probability=probability,
                    process_duration=process_duration
                )

        return components

    return model_function


def get_distribution(distribution_config):
    if not distribution_config or not distribution_config.get('type'):
        return None  # No distribution specified

    dist_type = distribution_config.get('type')
    params = distribution_config.get('params', {})

    if dist_type == 'triangular':
        low = float(params['low'])
        high = float(params['high'])
        mode = float(params['mode'])
        return (random.triangular, low, high, mode)
    elif dist_type == 'uniform':
        low = float(params['low'])
        high = float(params['high'])
        return (random.uniform, low, high)
    elif dist_type == 'expovariate':
        lambd = float(params['lambda'])
        return (random.expovariate, lambd)
    elif dist_type == 'normalvariate':
        mu = float(params['mu'])
        sigma = float(params['sigma'])
        return (random.normalvariate, mu, sigma)
    else:
        raise ValueError(f"Unsupported distribution type: {dist_type}")


def main():
    config_path = r"E:\projects\SEP_DMPG\src\util\flask\user\thoadelt\TestModellPCB\TestScenarioArrivalTable\TestModellPCB_TestScenarioArrivalTable.json"
    model_function = build_model_from_config(config_path)
    run_simulation(model=model_function, minutes=900, store_pivot_in_file=r"E:\projects\SEP_DMPG\src\util\builder_result.csv")
    # visualize_system()


if __name__ == '__main__':
    main()
