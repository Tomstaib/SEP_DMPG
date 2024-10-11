import unittest
from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
from src.util.global_imports import random
from src.util.simulations import run_simulation, run_replications


def setup_model4_1(env):
    source1 = Source(env, "Source1", (random.expovariate, 1 / 1.25))
    server1 = Server(env, "Server1", (random.expovariate, 1))
    sink1 = Sink(env, "Sink1")

    source1.connect(server1)
    server1.connect(sink1)


class TestCases(unittest.TestCase):

    def test_single_run(self):
        pivot_table = run_simulation(model=setup_model4_1, minutes=1440)                                   # 1 day
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'], 6.0149)  # 6.0036 ?

    def test_sequential_replications(self):
        pivot_table = run_replications(model=setup_model4_1, minutes=1440, num_replications=10, multiprocessing=False)

        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'], 4.5494)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'], 6.3527)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'], 9.0393)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Half-Width'], 0.7419)

    def test_parallel_replications(self):
        pivot_table = run_replications(model=setup_model4_1, minutes=1440, num_replications=10, multiprocessing=True)

        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'], 4.5494)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'], 6.3527)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'], 9.0393)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Half-Width'], 0.7419)
