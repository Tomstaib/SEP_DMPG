import argparse
import json
import os
import random

from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
from src.util.simulations import run_simulation, run_replications

"""def build_model_from_config(config_path):
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

                print(target_component, probability, process_duration)
                component.connect(
                    target_component,
                    probability=probability,
                    process_duration=process_duration
                )

        return components

    return model_function"""


def load_config(config_path: str | bytes):  # LiteralString as typehint because of os.path.join
    """Load configuration from the specified file path."""
    with open(config_path, 'r') as f:
        return json.load(f)


def get_component_id(component_config) -> str:
    """Get the unique ID for a component."""
    return component_config.get('id', component_config['name'])


def resolve_arrival_table_path(flask_base_path, arrival_table_path) -> str | bytes:  # LiteralString as typehint because of os.path.join
    """Resolve the absolute path for the arrival table if needed."""
    if arrival_table_path and not os.path.isabs(arrival_table_path) and not arrival_table_path.startswith("user"):
        return os.path.join(flask_base_path, arrival_table_path)
    return arrival_table_path


def create_source(env, source_config, flask_base_path) -> (str, Source):
    """Create a Source component from the source configuration."""
    name: str = source_config['name']
    component_id: str = get_component_id(source_config)
    distribution = source_config['distribution']
    arrival_table_path: str | bytes = resolve_arrival_table_path(flask_base_path, source_config.get('arrival_table'))  # LiteralString as typehint because of os.

    interarrival_time_dist = get_distribution(distribution) if distribution['type'] != 'arrival_table' else None

    source: Source = Source(env, name, creation_time_distribution_with_parameters=interarrival_time_dist,
                    arrival_table_path=arrival_table_path)

    return component_id, source


def create_server(env, server_config) -> (str, Server):
    """Create a Server component from the server configuration."""
    unique_id = get_component_id(server_config)
    name = server_config['name']
    distribution = server_config.get('distribution', {})
    processing_time_dist = get_distribution(distribution) if distribution else None

    # Breakdown parameters
    breakdown_config = server_config.get('breakdown', {})
    breakdown_time_dist = get_distribution(
        breakdown_config.get('time_between_machine_breakdown')) if breakdown_config.get(
        'time_between_machine_breakdown') else None
    breakdown_duration_dist = get_distribution(
        breakdown_config.get('machine_breakdown_duration')) if breakdown_config.get(
        'machine_breakdown_duration') else None

    queue_order = server_config.get('queue_order', 'FIFO')

    server: Server = Server(
        env,
        name,
        processing_time_distribution_with_parameters=processing_time_dist,
        time_between_machine_breakdowns=breakdown_time_dist,
        machine_breakdown_duration=breakdown_duration_dist,
        queue_order=queue_order
    )

    return unique_id, server


def create_sink(env, sink_config) -> (str, Sink):
    """Create a Sink component from the sink configuration."""
    unique_id = get_component_id(sink_config)
    name = sink_config['name']
    addon_process_trigger = sink_config.get('addon_process_trigger', None)

    sink = Sink(env, name, addon_process_trigger=addon_process_trigger)

    return unique_id, sink


def setup_connections(components, component_config) -> None:
    """Set up connections for the given component."""
    component_id: str = get_component_id(component_config)
    component: Source | Server = components[component_id]

    for connection in component_config.get('connections', []):
        target_id = connection['target']
        target_component = components.get(target_id)

        if not target_component:
            raise ValueError(f"Target component '{target_id}' not found for connection.")

        probability = float(connection.get('probability')) if connection.get('probability') else None
        process_duration = float(connection.get('process_duration')) if connection.get('process_duration') else None

        component.connect(
            target_component,
            probability=probability,
            process_duration=process_duration
        )


# def build_model_from_config(config_path):
def model_function(env):
    config = load_config(get_config_path())
    components: dict = {}  # Dictionary to hold all components by unique ID
    flask_base_path = os.path.abspath(os.path.join(os.path.dirname(get_config_path()), '../flask'))

    # Create and store sources
    for source_config in config.get('sources', []):
        component_id, source = create_source(env, source_config, flask_base_path)
        components[component_id] = source

    # Create and store servers
    for server_config in config.get('servers', []):
        component_id, server = create_server(env, server_config)
        components[component_id] = server

    # Create and store sinks
    for sink_config in config.get('sinks', []):
        component_id, sink = create_sink(env, sink_config)
        components[component_id] = sink

    # Set up connections
    for component_config in config.get('sources', []) + config.get('servers', []):
        setup_connections(components, component_config)

    return components

#    return model_function



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


def get_config_path() -> str:
    return os.getenv('CONFIG_PATH')


def main(replications: int):
    # config_path = r"E:\projects\SEP_DMPG\src\util\flask\user\thoadelt\TestModellPCB\TestScenarioArrivalTable\TestModellPCB_TestScenarioArrivalTable.json"
    # model_function = build_model_from_config(config_path)
    # run_simulation(model=model_function, minutes=minutes, store_pivot_in_file=r"E:\projects\SEP_DMPG\src\util\builder_result.csv")
    config = load_config(get_config_path())
    minutes: int = int(config.get('minutes'))
    run_replications(model=model_function, minutes=minutes, num_replications=replications, multiprocessing=True)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Run simulation with replications and minutes")

    parser.add_argument('-r','--replications', type=int, default=10, help="Number of replications for the simulation")

    # parser.add_argument('-t','--time_to_simulate', type=int, default=900, help="Duration of the simulation in minutes")

    parser.add_argument('-c', '--config_path', type=str, required=False, default=r"E:\projects\SEP_DMPG\src\util\flask\user\thoadelt\TestModellPCB\TestScenarioArrivalTable\TestModellPCB_TestScenarioArrivalTable.json", help="The config_file you want to use")

    args = parser.parse_args()

    os.environ['CONFIG_PATH'] = args.config_path

    main(args.replications)
