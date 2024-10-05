import unittest
from unittest.mock import MagicMock
from src.core.resetable_named_object import ResetAbleNamedObjectManager
from src.core.model import Model, ComponentType


class TestModel(unittest.TestCase):

    def setUp(self):
        # Mock ResetAbleNamedObjectManager to test Model's behavior independently
        self.mock_reset_manager = MagicMock(spec=ResetAbleNamedObjectManager)

        # Initialize the Model instance
        self.model = Model()

        # Replace actual managers with mock for isolated behavior
        self.model.components = {
            ComponentType.SOURCES: self.mock_reset_manager,
            ComponentType.SERVERS: self.mock_reset_manager,
            ComponentType.SINKS: self.mock_reset_manager
        }

    def test_add_component_sources(self):
        # Add component to SOURCES and check if it was added
        component = "SourceComponent1"
        self.model.add_component(component, ComponentType.SOURCES)

        self.mock_reset_manager.add.assert_called_with(component)

    def test_add_component_servers(self):
        # Add component to SERVERS and check if it was added
        component = "ServerComponent1"
        self.model.add_component(component, ComponentType.SERVERS)

        self.mock_reset_manager.add.assert_called_with(component)

    def test_add_component_sinks(self):
        # Add component to SINKS and check if it was added
        component = "SinkComponent1"
        self.model.add_component(component, ComponentType.SINKS)

        self.mock_reset_manager.add.assert_called_with(component)

    def test_get_components(self):
        # Mock return values from managers
        self.mock_reset_manager.__str__.return_value = "MockManager"

        components = self.model.get_components()

        # Check that each component type has a corresponding manager string "MockManager"
        expected = {
            'Sources': 'MockManager',
            'Servers': 'MockManager',
            'Sinks': 'MockManager'
        }

        # We use str() on each component manager because __str__ is being mocked
        components_str = {k: str(v) for k, v in components.items()}

        self.assertEqual(components_str, expected)

    def test_add_invalid_component_type(self):
        # Attempt to add a component with an invalid type should raise an error
        with self.assertRaises(KeyError):
            self.model.add_component("InvalidComponent", "InvalidType")


if __name__ == "__main__":
    unittest.main()
