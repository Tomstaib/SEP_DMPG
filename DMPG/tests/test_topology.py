import simpy
import unittest
from src.core.entity import Entity, EntityManager
from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
from src.util.helper import validate_probabilities
from src.core.queue_orders import QueueOrders


class TestCases(unittest.TestCase):

    def setUp(self):
        self.env = simpy.Environment()

    def test_entity_initialization(self):
        # Test the initialization of an Entity object
        entity = Entity("TestEntity", 10)

        self.assertEqual(entity.name, "TestEntity", "Name is not correctly assigned")
        self.assertEqual(entity.creation_time, 10, "Creation time is not correctly assigned")
        self.assertIsNone(entity.destruction_time, "Destruction time should initially be None")

    def test_source_initialization(self):
        # Test the initialization of a Source object
        source = Source(self.env, "TestSource")
        assert source.env == self.env  # Check if environment is correctly assigned
        assert source.name == "TestSource"  # Check if name is correctly assigned
        assert len(source.next_component) == 0  # Next servers list should initially be empty

    def test_server_initialization(self):
        # Test the initialization of a Server object
        server = Server(self.env, "TestServer")
        assert server.env == self.env  # Check if environment is correctly assigned
        assert server.name == "TestServer"  # Check if name is correctly assigned
        assert server.queue_order == QueueOrders.FIFO  # Default queue order should be FIFO

    def test_sink_initialization(self):
        # Test the initialization of a Sink object
        sink = Sink(self.env, "TestSink")
        assert sink.env == self.env  # Check if environment is correctly assigned
        assert sink.name == "TestSink"  # Check if name is correctly assigned

    def test_entity_reset_all(self):
        # Test the reset_all class method of Entity
        Entity("Entity1", 10)
        Entity("Entity2", 20)
        EntityManager.destroy_all_entities()
        assert len(EntityManager.entities) == 0  # Check if all entities are cleared

    def test_source_connect(self):
        # Test the connect method of Source
        source = Source(self.env, "TestSource")
        server = Server(self.env, "TestServer")
        source.connect(server)
        assert len(source.next_component) == 1  # Check if server is correctly connected

    def test_source_validate_probabilities(self):
        # Test the validate_probabilities method of Source
        source = Source(self.env, "TestSource")
        server1 = Server(self.env, "Server1")
        server2 = Server(self.env, "Server2")
        source.connect(server1, 70)
        source.connect(server2, 30)
        validate_probabilities(source)
        assert sum(prob for _, prob in source.next_component) == 100  # Check if probabilities sum up to 100
