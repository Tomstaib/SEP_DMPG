import simpy
import unittest
from src.core.entity import Entity
from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
from src.util.global_imports import random


class TestCases(unittest.TestCase):

    def setUp(self):
        self.env = simpy.Environment()

    def test_entity_lifecycle(self):
        source = Source(self.env, "TestSource", (random.expovariate, 1 / 6))
        server = Server(self.env, "TestServer", (random.triangular, 3, 5, 4))
        sink = Sink(self.env, "TestSink")
        source.connect(server)
        server.connect(sink)

        simulation_time = 1000
        self.env.run(until=simulation_time)

        for entity in source.entities:
            # Check if entity has been created
            assert entity.creation_time is not None

    def test_server_processing_time(self):
        server = Server(self.env, "TestServer",
                        processing_time_distribution_with_parameters=(random.uniform, 5, 10))

        sink = Sink(self.env, "TestSink")
        server.connect(sink)

        entity = Entity("TestEntity", 0)
        server.process_entity(entity)
        self.env.run(until=20)

        # Check if the entity processing time is within the expected range

        self.assertTrue(5 <= server.total_processing_time <= 10,
                        "Server processing time is outside the expected range")

    def test_server_queue_management(self):
        server = Server(self.env, "TestServer", queue_order="FIFO")
        # Add entities to the server's queue
        for i in range(5):
            entity = Entity(f"Entity{i}", i)
            server.process_entity(entity)
        # Check if entities are queued in FIFO order
        for i, entity in enumerate(server.server_queue):
            self.assertEqual(entity.name, f"Entity{i}", f"{entity.name} != Entity{i}")

    def test_server_fifo_queue_management(self):
        server = Server(self.env, "TestServer",
                        processing_time_distribution_with_parameters=(random.uniform, 1, 5),
                        queue_order="FIFO")
        sink = Sink(self.env, "TestSink")
        server.connect(sink)

        for i in range(3):
            server.process_entity(Entity(f"Entity{i}", i))
        self.env.run(until=30)

        self.assertEqual(server.entities_processed, 3, "Server did not process all entities")

    def test_source_reset(self):
        # Test the reset method of Source
        source = Source(self.env, "TestSource")
        source.entities_created = 5
        source.reset()
        self.assertEqual(source.entities_created, 0, "entities_created was not resetted to 0")
        self.assertEqual(len(source.entities), 0, "entities list was not cleared")

    def test_sink_reset(self):
        # Test the reset method of Sink
        sink = Sink(self.env, "TestSink")
        sink.entities_processed = 4
        sink.reset()
        self.assertEqual(sink.entities_processed, 0, "entities_processed was not resetted to 0")

    def test_sink_process_entity(self):
        # Test the process_entity method of Sink
        sink = Sink(self.env, "TestSink")
        entity = Entity("TestEntity", 10)
        sink.process_entity(entity)
        self.assertEqual(sink.entities_processed, 1, "Entity was not processed")

    def test_end_to_end_workflow(self):
        source = Source(self.env, "TestSource", (random.expovariate, 1 / 6))
        server = Server(self.env, "TestServer", (random.triangular, 3, 5, 4))
        sink = Sink(self.env, "TestSink")

        source.connect(server)
        server.connect(sink)

        self.env.run(until=1000)

        # Check if at least one entity has been created, processed, and reached the sink.
        self.assertGreater(len(source.entities), 0, "No entities were created by the source")
        self.assertGreater(server.entities_processed, 0, "No entities were processed by the server")
        self.assertGreater(sink.entities_processed, 0, "No entities were processed by the sink")

    def test_server_processing_multiple_entities(self):
        server = Server(self.env, "TestServerMulti", (random.uniform, 1, 2))
        sink = Sink(self.env, "TestSinkMulti")
        server.connect(sink, 100)

        for i in range(5):
            server.process_entity(Entity(f"MultiEntity{i}", i))
        self.env.run(until=15)

        self.assertEqual(server.entities_processed, 5, "Server did not process all entities correctly")
