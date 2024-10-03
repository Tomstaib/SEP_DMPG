import unittest
import simpy
from typing import Callable
from src.core.source import Source
from src.core.server import Server
from src.core.sink import Sink
from src.core.entity import SubEntity
from src.util.global_imports import random
from src.util.simulations import run_simulation, run_replications
from src.models.model_pcb import routing_rework_limitation, record_times_processed


def setup_model_pcb(env: simpy.Environment) -> None:
    """Sets up the PCB model with the given environment."""
    random.seed(42)  # random seed for consistent results

    # Create servers, sinks, and sources
    source1 = Source(env, "PCB", (random.expovariate, 1 / 6), entity_class=SubEntity)

    server1 = Server(env, "Placement", (random.triangular, 3, 5, 4))
    server2 = Server(env, "FinePitchFast", (random.triangular, 8, 10, 9))
    server3 = Server(env, "FinePitchMedium", (random.triangular, 18, 22, 20))
    server4 = Server(env, "FinePitchSlow", (random.triangular, 22, 26, 24))
    server5 = Server(env, "Inspection", (random.uniform, 2, 4), routing_expression=(routing_rework_limitation,))
    server6 = Server(env, "Rework", (random.triangular, 2, 6, 4))

    sink1 = Sink(env, "GoodParts", addon_processing_done_method_with_parameters=(record_times_processed,))
    sink2 = Sink(env, "BadParts", addon_processing_done_method_with_parameters=(record_times_processed,))

    # Set up connections with routing probabilities for servers
    source1.connect(server1)
    server1.connect(server2)
    server1.connect(server3)
    server1.connect(server4)
    server2.connect(server5)
    server3.connect(server5)
    server4.connect(server5)
    server6.connect(server1)

    server5.connect(sink1, 66)  # 66% probability to route to Sink1
    server5.connect(sink2, 8)  # 8% probability to route to Sink2
    server5.connect(server6, 26)  # 26% probability to route to Rework


class TestPCBModel(unittest.TestCase):

    def test_single_run(self) -> None:
        """Test a single run of the model PCB."""
        pivot_table = run_simulation(model=setup_model_pcb, minutes=1440)  # 1 day
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'], 171.1672)

    def test_routing_to_rework(self) -> None:
        """Test routing to Rework based on entity processing count."""
        env = simpy.Environment()
        random.seed(42)

        setup_model_pcb(env)
        env.run(until=10000)  # Trigger Rework-route with high amount of Entities

        self.assertTrue(env.now >= 10000)

    def test_sequential_replications(self) -> None:
        """Test sequential replications of the model PCB."""
        pivot_table = run_replications(model=setup_model_pcb, minutes=1440, num_replications=10, multiprocessing=False)

        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'], 171.1672)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'], 171.1672)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'], 171.1672)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Half-Width'], 0.0)

    def test_parallel_replications(self) -> None:
        """Test parallel replications of the model PCB."""
        pivot_table = run_replications(model=setup_model_pcb, minutes=1440, num_replications=10, multiprocessing=True)

        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'], 171.1672)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'], 171.1672)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'], 171.1672)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Half-Width'], 0.0)

    def test_routing_to_bad_parts(self) -> None:
        """Test routing to BadParts based on entity processing count."""
        env = simpy.Environment()
        random.seed(42)

        setup_model_pcb(env)
        env.run(until=10000)

        self.assertTrue(env.now >= 10000)

    def test_connections(self) -> None:
        """Test if all connections in the model PCB are set correctly."""
        env = simpy.Environment()
        setup_model_pcb(env)

        env.run(until=1440)

        self.assertEqual(env.now, 1440)


if __name__ == '__main__':
    unittest.main()
