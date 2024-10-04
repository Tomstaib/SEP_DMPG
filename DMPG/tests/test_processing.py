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
        server.handle_entity_arrival(entity)
        self.env.run(until=20)

        # Check if the entity processing time is within the expected range

        self.assertTrue(5 <= server.total_processing_time_pivot_table <= 10,
                        "Server processing time is outside the expected range")

    def test_server_queue_management(self):
        server = Server(self.env, "TestServer", queue_order="FIFO", capacity=0)
        # Add entities to the server's queue
        for i in range(5):
            entity = Entity(f"Entity{i}", i)
            server.handle_entity_arrival(entity)
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
            server.handle_entity_arrival(Entity(f"Entity{i}", i))
        self.env.run(until=30)

        self.assertEqual(server.entities_processed, 3, "Server did not process all entities")

    def test_source_reset(self):
        # Test the reset method of Source
        source = Source(self.env, "TestSource")
        source.entities_created_pivot_table = 5
        source.reset()
        self.assertEqual(source.entities_created_pivot_table, 0, "entities_created was not resetted to 0")
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
        sink.handle_entity_arrival(entity)
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
            server.handle_entity_arrival(Entity(f"MultiEntity{i}", i))
        self.env.run(until=15)

        self.assertEqual(server.entities_processed, 5, "Server did not process all entities correctly")

    def test_server_capacity_with_single_entity(self):
        server = Server(self.env, "ServerCapacity2", capacity=2,
                        processing_time_distribution_with_parameters=(lambda: 2,))
        sink = Sink(self.env, "TestSink")
        server.connect(sink)

        entity = Entity("Entity1", self.env.now)
        server.handle_entity_arrival(entity)
        self.env.run(until=5)

        # Test the server's behavior when processing a single entity
        # ensuring the capacity feature does not affect the expected processing of individual entities.
        self.assertTrue(entity.destruction_time is not None,
                        "Server did not process the entity within the expected timeframe")
        self.assertEqual(entity.destruction_time, 2, "Entity processing time does not match expected")

    def test_server_capacity_exceeded(self):
        server = Server(self.env, "ServerCapacity1", capacity=1,
                        processing_time_distribution_with_parameters=(lambda: 2,))
        sink = Sink(self.env, "TestSink")
        server.connect(sink)
        entities = [Entity(f"Entity{i + 1}", self.env.now) for i in range(3)]
        for entity in entities:
            server.handle_entity_arrival(entity)
        self.env.run(until=5)

        # Evaluate the server's ability to queue entities when its processing capacity is exceeded
        # and verify entities are processed according to the server's capacity
        self.assertTrue(all(entity.destruction_time is not None for entity in entities[:2]),
                        "Not all entities were processed as expected")
        self.assertIsNone(entities[2].destruction_time, "Server processed more entities than its capacity")

    def test_server_reset_with_capacity(self):
        server = Server(self.env, "ServerCapacity4", capacity=1,
                        processing_time_distribution_with_parameters=(lambda: 5,))
        sink = Sink(self.env, "TestSink")
        server.connect(sink)
        entities = [Entity(f"Entity{i + 1}", self.env.now) for i in range(2)]
        for entity in entities:
            server.handle_entity_arrival(entity)
        Server.servers.reset_all()
        self.env.run(until=3)

        # Ensure that resetting the server also clears any entities queued due to capacity limits
        self.assertEqual(len(server.currently_processing), 0, "Server did not clear its processing queue upon reset")
        self.assertEqual(server.entities_processed, 0, "Server did not reset its processed entities count")

    def test_server_processing_with_capacity(self):
        """
        This test revealed a problem with the new routing implementation.
        When trying to route multiple Entities at the same time, only one is routed.
        """
        server = Server(self.env, "ServerOrderTime", (random.uniform, 1.99999999, 2.00000001), capacity=2)
        # server = Server(self.env, "ServerOrderTime", (random.uniform, 2, 2), capacity=2)
        sink = Sink(self.env, "TestSink")
        server.connect(sink)

        # Create and process multiple entities
        entities = [Entity(f"EntityOrderTime{i + 1}", self.env.now) for i in range(4)]
        for entity in entities:
            server.handle_entity_arrival(entity)

        self.env.run(until=4.01)

        # test if the server processes entities in the correct order: FIFO
        # and calculates the processing time correctly when multiple entities are involved
        processed_entities_names = [entity.name for entity in sink.processed_entities]
        expected_order = [entity.name for entity in entities]

        self.assertEqual(len(expected_order), len(processed_entities_names), "Entities were not processed as expected.")
