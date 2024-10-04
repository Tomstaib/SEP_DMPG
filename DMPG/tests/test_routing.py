import unittest
from src.core.entity import EntityManager
from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
import simpy
from src.util.simulations import run_simulation
from src.util.global_imports import random


def routing_smallest_queue(routing_object, entity, *parameters):
    smallest_queue = 999_999
    next_server_via = None
    for connection in routing_object.connections:
        if len(routing_object.connections[connection].next_component.server_queue) < smallest_queue:
            smallest_queue = len(routing_object.connections[connection].next_component.server_queue)
            next_server_via = routing_object.connections[connection]
    next_server_via.handle_entity_arrival(entity)


def setup_model_with_processing_durations(env):
    source1 = Source(env, "Source1", (random.expovariate, 1 / 1.25))
    server1 = Server(env, "Server1", (random.expovariate, 1))
    sink1 = Sink(env, "Sink1")

    source1.connect(server1, travel_duration=0.1)
    server1.connect(sink1, travel_duration=0.2)


def setup_model_without_processing_durations(env):
    source1 = Source(env, "Source1", (random.expovariate, 1 / 1.25))
    server1 = Server(env, "Server1", (random.expovariate, 1))
    sink1 = Sink(env, "Sink1")

    source1.connect(server1, travel_duration=0)
    server1.connect(sink1, travel_duration=0)


def setup_model_with_routing_expression(env):
    source1 = Source(env, "Source1", (random.expovariate, 1 / 1.25), routing_expression=(routing_smallest_queue,))
    server1 = Server(env, "Server1", (random.expovariate, 0.3))
    server2 = Server(env, "Server2", (random.expovariate, 1))
    sink1 = Sink(env, "Sink1")

    source1.connect(server1)
    source1.connect(server2)
    server1.connect(sink1)
    server2.connect(sink1)


class TestCases(unittest.TestCase):

    def setUp(self):
        self.env = simpy.Environment()

    def test_connection(self):
        source = Source(self.env, "TestSource")
        server = Server(self.env, "TestServer")
        source.connect(server)
        assert len(source.connections) == 1  # Check if server is correctly connected

    def test_routing_object_connection(self):
        source = Source(self.env, "TestSource")
        server = Server(self.env, "TestServer")
        source.connect(server, travel_duration=10)
        self.assertEqual(source.connections['TestServer'].travel_duration, 10)
        self.assertEqual(source.connections['TestServer'].next_component.name, 'TestServer')
        self.assertEqual(source.connections['TestServer'].origin_component.name, 'TestSource')

    def test_single_run_with_processing_time(self):
        EntityManager.destroy_all_entities()
        pivot_table = run_simulation(model=setup_model_with_processing_durations, minutes=1440)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'], 152.6990)

    def test_single_run_with_processing_time_set_zero(self):
        EntityManager.destroy_all_entities()
        pivot_table = run_simulation(model=setup_model_without_processing_durations, minutes=1440)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'], 6.0036)

    def test_single_run_route_smallest_queue(self):
        EntityManager.destroy_all_entities()
        # AvgTimeProcessing to be changed after server reset implementation
        pivot_table = run_simulation(model=setup_model_with_routing_expression, minutes=1440)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'], 4.1928)
        self.assertAlmostEqual(pivot_table.at[('Server', 'Server1', 'AvgTimeProcessing'), 'Value'], 3.4969)
        self.assertEqual(pivot_table.at[('Server', 'Server2', 'AvgTimeProcessing'), 'Value'], 1.0351)
