from src.util.global_imports import random
from src.core.source import RL_Source
from src.core.server import Server
from src.core.sink import Sink
from src.core.entity import SubEntity
from src.util.simulations import run_simulation


def record_times_processed(routing_object, entity, *parameters):
    routing_object.tally_statistic.record(entity.num_times_processed)


def routing_rework_limitation(routing_object, entity, *parameters):
    if isinstance(entity, SubEntity) and entity.num_times_processed == 11:
        for server_probability in routing_object.connection_cache:
            if routing_object.connection_cache[server_probability].name == 'BadParts':
                next_server = routing_object.connection_cache[server_probability]
                next_server.handle_entity_arrival(entity)
                routing_object.number_exited_pivot_table += 1
    else:
        decision = random.uniform(0, 100)
        for cumulative_probability in routing_object.connection_cache:
            if decision <= cumulative_probability:
                next_server_via = routing_object.connection_cache[cumulative_probability]
                next_server_via.handle_entity_arrival(entity)
                break


def setup_model_pcb(env, params):
    # Create servers, sinks, and sources

    source1 = RL_Source(env, "PCB", params)
    server1 = Server(env, "Placement", (random.triangular, 8, 10, 12))
    sink1 = Sink(env, "GoodParts")

    source1.connect(server1)

    server1.connect(sink1)


def main():
    run_simulation(model=setup_model_pcb, minutes=1440)                                      # 1 day
    # print(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'])               # 6.0036


if __name__ == '__main__':
    main()
