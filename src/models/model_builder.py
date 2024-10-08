import argparse
import os
import random
from typing import Callable
import simpy
from src.core.queue_type import QueueType
from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
from src.util.simulations import run_replications
from src.util.helper import load_config


def get_component_id(component_config: dict) -> str:
    """
    Get the unique ID for a component.

    :param component_config: Dictionary containing the component's configuration.
    :return: The unique ID for the component, defaults to 'name' if 'id' is not provided.
    """  # noqa: E501
    return component_config.get('id', component_config['name'])


def resolve_arrival_table_path(flask_base_path: str,
                               arrival_table_path: str) -> str:
    """
    Resolve the absolute path for the arrival table if needed.

    :param flask_base_path: The base path where Flask application data is stored.
    :param arrival_table_path: The path to the arrival table, which may be relative or absolute.
    :return: Absolute path to the arrival table, or the input path if it's already absolute.
    """  # noqa: E501
    if (arrival_table_path and not os.path.isabs(arrival_table_path)
            and not arrival_table_path.startswith("user")):
        return os.path.join(flask_base_path, arrival_table_path)
    return arrival_table_path


def create_source(env: simpy.Environment, source_config: dict,
                  flask_base_path: str) -> (str, Source):
    """
    Create a Source component from the source configuration.

    :param env: Simpy environment in which the source component will operate.
    :param source_config: Dictionary containing the configuration for the source.
    :param flask_base_path: Base path for the Flask application, used to resolve arrival table paths.
    :return: A tuple containing the unique ID of the source component and the Source object.
    
    See also:
        - [Source](../core/source.html): A source is a component that creates entities and routes them to the next component.
    """  # noqa: E501
    name: str = source_config['name']
    component_id: str = get_component_id(source_config)
    distribution = source_config['distribution']
    arrival_table_path: str = resolve_arrival_table_path(
        flask_base_path,
        source_config.get('arrival_table'))

    interarrival_time_dist = get_distribution(
        distribution) if distribution['type'] != 'arrival_table' else None

    source: Source = Source(
        env, name,
        creation_time_distribution_with_parameters=interarrival_time_dist,
        arrival_table_path=arrival_table_path)

    return component_id, source


def create_server(env: simpy.Environment,
                  server_config: dict) -> (str, Server):
    """
    Create a Server component from the server configuration.

    :param env: Simpy environment in which the server component will operate.
    :param server_config: Dictionary containing the configuration for the server.

    :return: UniqueID and Server object
    
    See also:
        - [Server](../core/server.html): Represents a server in a simulation environment.
    """  # noqa: E501
    unique_id: str = get_component_id(server_config)
    name: str = server_config['name']
    distribution = server_config.get('distribution', {})
    processing_time_dist = get_distribution(
        distribution) if distribution else None

    # Breakdown parameters
    breakdown_config = server_config.get('breakdown', {})
    breakdown_time_dist = get_distribution(
        breakdown_config.get(
            'time_between_machine_breakdown')) if breakdown_config.get(
        'time_between_machine_breakdown') else None
    breakdown_duration_dist = get_distribution(
        breakdown_config.get(
            'machine_breakdown_duration')) if breakdown_config.get(
        'machine_breakdown_duration') else None

    queue_order: QueueType = QueueType(
        server_config.get('queue_order', 'FIFO'))

    server: Server = Server(
        env,
        name,
        processing_time_distribution_with_parameters=processing_time_dist,
        time_between_machine_breakdowns=breakdown_time_dist,
        machine_breakdown_duration=breakdown_duration_dist,
        queue_order=queue_order
    )

    return unique_id, server


def create_sink(env: simpy.Environment, sink_config: dict) -> (str, Sink):
    """
    Create a Sink component from the sink configuration.

    :param env: Simpy environment in which the server component will operate.
    :param sink_config: Dictionary containing the configuration for the sink.

    :return: UniqueID and Sink object
    
    See also:
        - [Sink](../core/sink.html): Represents a sink in a simulation environment.
    """  # noqa: E501
    unique_id: str = get_component_id(sink_config)
    name: str = sink_config['name']
    addon_process_trigger = None

    sink: Sink = Sink(env, name, addon_processing_done_method_with_parameters=addon_process_trigger)

    return unique_id, sink


def setup_connections(components: dict, component_config: dict) -> None:
    """
    Set up connections for the given component.

    :param components: Dictionary containing all components and their ids.
    :param component_config: Dictionary containing the component's configuration.
    
    See also:
        - [Connection](../core/connection.html): Connects simulation components.
        - [RoutingObject](../core/routing_object.html)
    """  # noqa: E501
    component_id: str = get_component_id(component_config)
    component: Source | Server = components[component_id]

    for connection in component_config.get('connections', []):
        target_id: str = connection['target']
        target_component: Source | Server | Sink = components.get(target_id)

        if not target_component:
            raise ValueError(
                f"Target component '{target_id}' not found for connection.")

        probability = float(connection.get('probability')) if connection.get(
            'probability') else None
        process_duration = float(
            connection.get('process_duration')) if connection.get(
            'process_duration') else None

        component.connect(
            target_component,
            probability=probability,
            process_duration=process_duration
        )


def model_function(env: simpy.Environment) -> dict:
    """
    Build a model from the provided configuration file.

    :param env: Simpy environment of the simulation
    
    See also:
        - [Source](../core/source.html)
        - [Server](../core/server.html)
        - [Sink](../core/sink.html)
        - [RoutingObject](../core/routing_object.html)
        - [Model](../core/model.html#Model)
    """  # noqa: E501
    config: dict = load_config(get_config_path())
    components: dict = {}  # Dictionary to hold all components by unique ID
    flask_base_path = os.path.abspath(
        os.path.join(os.path.dirname(get_config_path()), '../flask'))

    # Create and store sources
    for source_config in config.get('sources', []):
        component_id, source = create_source(env, source_config,
                                             flask_base_path)
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
    for component_config in config.get('sources', []) + config.get('servers',
                                                                   []):
        setup_connections(components, component_config)

    return components


def get_distribution(distribution_config: dict) -> (Callable, ...):
    """
    Get the distribution with parameters from the configuration file.

    :param distribution_config: Dictionary containing the parameters for the distribution.
    """  # noqa: E501
    if not distribution_config or not distribution_config.get('type'):
        return None  # No distribution specified

    dist_type: str = distribution_config.get('type')
    params: dict = distribution_config.get('params', {})

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
    """
    Get the path to the configuration file stored in the environment variables.
    This is necessary because multiple processes are accessing this variable.

    :return: Path to the configuration file.
    """
    return os.getenv('CONFIG_PATH')


def main(replications: int):
    """
    Run the model builder.

    :param replications: Number of replications for the simulation

    See also:
        - [run_replications](../util/simulations.html#run_replications): Run replications of a model.
    """
    config = load_config(get_config_path())
    minutes: int = int(config.get('minutes'))
    run_replications(model=model_function, minutes=minutes,
                     num_replications=replications, multiprocessing=True, save_to_database=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Run simulation with replications and minutes")

    parser.add_argument('-r', '--replications', type=int,
                        default=10,
                        help="Number of replications for the simulation")

    parser.add_argument('-c', '--config_path', type=str,
                        required=True,
                        help="The config_file you want to use")

    args = parser.parse_args()

    os.environ['CONFIG_PATH'] = args.config_path
    """Store the path to the configuration file in the environment variables."""  # noqa: E501

    main(args.replications)
