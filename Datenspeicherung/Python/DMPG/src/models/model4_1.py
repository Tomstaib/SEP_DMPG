from src.util.global_imports import random
from src.core.source import Source
from src.core.server import Server
from src.core.sink import Sink
from src.util.simulations import run_simulation, run_replications


def setup_model4_1(env):

    source1 = Source(env, "Source1", (random.expovariate, 1 / 1.25))
    server1 = Server(env, "Server1", (random.expovariate, 1))
    sink1 = Sink(env, "Sink1")

    source1.connect(server1)
    server1.connect(sink1)


def main():
    run_simulation(model=setup_model4_1, minutes=1440, store_pivot_in_file='simulation_results.csv')                                      # 1 day
    # print(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'])               # 6.0036

    # 1 week ~ 0:03.3 iteration & 0:33 total
    #run_replications(model=setup_model4_1, minutes=10080, num_replications=100, multiprocessing=False)

    # 1 year ~ 0:25 iteration & 4:00 total
    #run_replications(model=setup_model4_1, minutes=525600, num_replications=1000, multiprocessing=True)
    """
    print(pivot_table3.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'])
    print(pivot_table3.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'])
    print(pivot_table3.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'])
    print(pivot_table3.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Half-Width'])
    """


if __name__ == '__main__':
    main()
