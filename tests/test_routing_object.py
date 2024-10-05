import unittest
from unittest.mock import MagicMock, patch
from src.core.routing_object import RoutingObject
# Mock random.uniform
import random
random.uniform = MagicMock()


# Mock the Entity class
class Entity:
    pass

# Mock the Source class
class Source:
    pass

# Mock the Connection class
class Connection:
    def __init__(self, env, from_component, to_component, name, process_duration, probability):
        self.env = env
        self.from_component = from_component
        self.to_component = to_component
        self.name = name
        self.process_duration = process_duration
        self.probability = probability


class TestRoutingObject(unittest.TestCase):

    def setUp(self):
        # Set up a mock environment
        self.env = MagicMock()

    def test_init(self):
        """Test that the __init__ method initializes all variables correctly."""
        routing_expression = MagicMock()
        routing_object = RoutingObject(self.env, routing_expression)
        self.assertEqual(routing_object.env, self.env)
        self.assertEqual(routing_object.routing_expression, routing_expression)
        self.assertEqual(routing_object.next_components, [])
        self.assertEqual(routing_object.number_exited, 0)
        self.assertEqual(routing_object.connection_cache, {})
        self.assertEqual(routing_object.connections, {})

    def test_route_entity_with_routing_expression(self):
        """Test route_entity when routing_expression is provided."""
        func = MagicMock()
        routing_expression = [func, 'arg1', 'arg2']
        routing_object = RoutingObject(self.env, routing_expression)
        entity = Entity()
        routing_object.route_entity(entity)
        func.assert_called_once_with(routing_object, entity, 'arg1', 'arg2')

    @patch('random.uniform')
    def test_route_entity_without_routing_expression(self, mock_uniform):
        """Test route_entity when routing_expression is None."""
        routing_object = RoutingObject(self.env)
        entity = Entity()
        # Set up connection_cache
        mock_server1 = MagicMock()
        mock_server1.process_entity = MagicMock()
        mock_server2 = MagicMock()
        mock_server2.process_entity = MagicMock()
        routing_object.connection_cache = {
            50: mock_server1,
            100: mock_server2
        }
        # Test decision <= 50
        mock_uniform.return_value = 30
        routing_object.route_entity(entity)
        mock_server1.handle_entity_arrival.assert_called_once_with(entity)
        mock_server2.handle_entity_arrival.assert_not_called()
        # Reset mocks
        mock_server1.handle_entity_arrival.reset_mock()
        mock_server2.handle_entity_arrival.reset_mock()
        # Test 50 < decision <= 100
        mock_uniform.return_value = 70
        routing_object.route_entity(entity)
        mock_server1.handle_entity_arrival.assert_not_called()
        mock_server2.handle_entity_arrival.assert_called_once_with(entity)

    @patch('random.uniform')
    def test_route_entity_no_match_in_connection_cache(self, mock_uniform):
        """Test route_entity when no cumulative_probability matches the decision."""
        routing_object = RoutingObject(self.env)
        entity = Entity()
        mock_server1 = MagicMock()
        routing_object.connection_cache = {
            50: mock_server1,
        }
        mock_uniform.return_value = 70
        routing_object.route_entity(entity)
        mock_server1.handle_entity_arrival.assert_not_called()

    def test_connect_valid_next_server(self):
        """Test connect method with a valid next server."""
        routing_object = RoutingObject(self.env)
        next_server = MagicMock()
        next_server.name = 'NextServer'
        with patch('src.core.connection.Connection', new=Connection):
            routing_object.connect(next_server, probability=0.5, process_duration=10)
            self.assertIn((next_server, 0.5), routing_object.next_components)
            self.assertIn('NextServer', routing_object.connections)
            connection = routing_object.connections['NextServer']
            self.assertEqual(connection.env, self.env)
            self.assertEqual(connection.from_component, routing_object)
            self.assertEqual(connection.to_component, next_server)
            self.assertEqual(connection.name, 'NextServer')
            self.assertEqual(connection.process_duration, 10)
            self.assertEqual(connection.probability, 0.5)

    def test_connect_with_source_raises_value_error(self):
        """Test connect method raises ValueError when next_server is a Source instance."""
        routing_object = RoutingObject(self.env)
        next_server = Source()
        # Patch the 'Source' in the connect method's global namespace
        with patch('src.core.source.Source', Source):
            with self.assertRaises(ValueError) as context:
                routing_object.connect(next_server)
        self.assertEqual(str(context.exception), "Next component must be a Server or Sink")

if __name__ == '__main__':
    unittest.main()
