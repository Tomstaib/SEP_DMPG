import unittest
import simpy
from src.core.entity import EntityManager
from src.util.global_imports import random
from src.core.source import Source
from src.core.server import Server
from src.core.sink import Sink
from src.core.entity import SubEntity
from src.util.simulations import run_simulation
from src.core.tally_statistic import TallyStatistic


def record_times_processed(routing_object, entity, *parameters):
    routing_object.tally_statistic.record(entity.num_times_processed)


def routing_rework_limitation(routing_object, entity, *parameters):
    if isinstance(entity, SubEntity) and entity.num_times_processed == 11:
        for server_probability in routing_object.connection_cache:
            if routing_object.connection_cache[server_probability].name == 'BadParts':
                next_server = routing_object.connection_cache[server_probability]
                next_server.process_entity(entity)
                routing_object.number_exited_pivot_table += 1
    else:
        decision = random.uniform(0, 100)
        for cumulative_probability in routing_object.connection_cache:
            if decision <= cumulative_probability:
                next_server_via = routing_object.connection_cache[cumulative_probability]
                next_server_via.process_entity(entity)
                break


def setup_model_pcb(env):
    # Create servers, sinks, and sources
    source1 = Source(env, "PCB", (random.expovariate, 1 / 6),
                     entity_class=SubEntity)

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
    server5.connect(sink2, 8)  # 8% probability to route to Sink1
    server5.connect(server6, 26)  # 26% probability to route to Rework


class TestCases(unittest.TestCase):

    def setUp(self):
        self.tally_statistic = TallyStatistic()
        self.env = simpy.Environment()
        self.entity_sub_class = SubEntity

    def test_single_run_statistics(self):
        EntityManager.destroy_all_entities()
        pivot_table = run_simulation(model=setup_model_pcb, minutes=1440)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'], 185.9660)

        self.assertEqual(pivot_table.at[('Sink', 'GoodParts', 'NumTimesProcessed_Avg'), 'Value'], 3.8054)
        self.assertEqual(pivot_table.at[('Sink', 'GoodParts', 'NumTimesProcessed_Max'), 'Value'], 7.0)
        self.assertEqual(pivot_table.at[('Sink', 'GoodParts', 'NumTimesProcessed_Min'), 'Value'], 3.0)

        self.assertEqual(pivot_table.at[('Sink', 'BadParts', 'NumTimesProcessed_Avg'), 'Value'], 5.8889)
        self.assertEqual(pivot_table.at[('Sink', 'BadParts', 'NumTimesProcessed_Max'), 'Value'], 11.0)
        self.assertEqual(pivot_table.at[('Sink', 'BadParts', 'NumTimesProcessed_Min'), 'Value'], 3.0)

    def test_record(self):
        self.tally_statistic.record(5)
        self.assertEqual(self.tally_statistic.num_times_processed_list, [5], 'tally statistics are not fillled')

    def test_entity_class(self):
        source = Source(self.env, "TestSource", (random.expovariate, 1 / 6),
                        entity_class=self.entity_sub_class)
        server = Server(self.env, "TestServer", (random.triangular, 3, 5, 4))
        sink = Sink(self.env, "TestSink")
        source.connect(server)
        server.connect(sink)

        simulation_time = 1000
        self.env.run(until=simulation_time)

        for entity in source.entities:
            assert issubclass(entity.__class__, SubEntity)
            self.assertTrue(issubclass(entity.__class__, SubEntity), 'entities are no subentities (subclass)')
