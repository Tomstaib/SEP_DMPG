import unittest
from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
from src.util.global_imports import random, set_duration_warm_up
from src.util.simulations import run_simulation


def setup_model4_1(env):
    source1 = Source(env, "Source1", (random.expovariate, 1 / 1.25))
    server1 = Server(env, "Server1", (random.expovariate, 1))
    sink1 = Sink(env, "Sink1")

    source1.connect(server1)
    server1.connect(sink1)


class TestCases(unittest.TestCase):

    def test_warm_up(self):
        pivot_table = run_simulation(model=setup_model4_1, minutes=1440, warm_up=15)        # 1 day
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'], 6.03)
        set_duration_warm_up(0)
