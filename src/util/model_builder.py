import json
import random

from core.server import Server
from core.sink import Sink
from core.source import Source
from util.simulations import run_simulation


def build_model_from_config(config_path):
    def model_function(env):
        # Load the configuration file
        with open(config_path, 'r') as f:
            config = json.load(f)

        components = {}  # Dictionary to hold all components by unique ID

        # Function to get component unique ID
        def get_component_id(component_config):
            return component_config.get('id', component_config['name'])

        # Create sources
        for source_config in config.get('sources', []):
            unique_id = get_component_id(source_config)
            name = source_config['name']
            distribution = source_config.get('distribution', {})
            arrival_table_path = source_config.get('arrival_table')

            # Determine interarrival time distribution
            interarrival_time_dist = get_distribution(distribution) if distribution else None

            source = Source(
                env,
                name,
                creation_time_distribution_with_parameters=interarrival_time_dist,
                arrival_table_path=arrival_table_path
            )
            components[unique_id] = source

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
    if not distribution_config:
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
    config_path = r"E:\projects\SEP_DMPG\src\util\flask\user\thoadelt\TestModell\TestScenario3\TestModell_TestScenario3.json"
    model_function = build_model_from_config(config_path)
    run_simulation(model=model_function, minutes=900)


if __name__ == '__main__':
    main()
r"""Traceback (most recent call last):
  File "E:\projects\SEP_DMPG\src\util\model_builder.py", line 110, in <module>
    main()
  File "E:\projects\SEP_DMPG\src\util\model_builder.py", line 106, in main
    run_simulation(model=model_function, minutes=900)
  File "E:\projects\SEP_DMPG\src\util\simulations.py", line 44, in run_simulation
    model(env)
  File "E:\projects\SEP_DMPG\src\util\model_builder.py", line 66, in model_function
    component.connect(target_component, probability, process_duration)
  File "E:\projects\SEP_DMPG\src\core\routing_object.py", line 32, in connect
    self.connections[next_server.name] = Connection(self.env, self, next_server, next_server.name, process_duration, probability)
AttributeError: 'NoneType' object has no attribute 'name'"""