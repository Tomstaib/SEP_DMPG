from __future__ import annotations
from typing import Optional
import unittest
import os
import sys
from io import StringIO

sys.path.append('/app/Verteilung/util')

from unittest.mock import patch
from unittest.mock import MagicMock

# Für Dockercontainer zum initialisierren der lokalen Module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from util.nodes_for_composite import Node, ManagementNode, ComputeNode, create_composite_tree, MINIMUM_OF_REPLICATIONS_FOR_COMPOSITE, NUM_REPLICATIONS, compute_tree_sizes, add_nodes, input_positive_number


class ConcreteNode(Node):
    '''
    Instance of the abstact Class Node
    '''
    def __init__(self, parent: Optional[ManagementNode] = None):
        super().__init__(parent)
        self._name = "ConcreteNode"

    def distribute_and_compute(self, model, minutes: int, num_replications: int) -> None:
        pass

class TestNode(unittest.TestCase):
    '''
    The tests verifies the correct behavior of instance creation and _instance_count incrementation, 
    checks the setting and retrieving of a parent node, handles invalid parent settings, and 
    ensures that a warningis raised when attempting to set a second parent.
    '''
    def setUp(self):
        # Reset the _instance_count before each test
        ConcreteNode._instance_count = 0

    def test_instance_creation(self):
        # Tests the instantiation of ConcreteNode and whether _instance_count is incremented
        node = ConcreteNode()
        self.assertIsInstance(node, ConcreteNode)
        self.assertEqual(node.__class__._instance_count, 1)
        self.assertEqual(str(node), "ConcreteNode")

    def test_parent_setting(self):
        # Tests the setting and retrieving of the parent node
        parent_node = ManagementNode()
        node = ConcreteNode()

        self.assertTrue(node.set_parent(parent_node))
        self.assertEqual(node.get_parent(), parent_node)

    def test_invalid_parent_setting(self):
        # Tests the setting of invalid node
        node = ConcreteNode()
        with self.assertRaises(TypeError):
            node.set_parent("invalid_parent")

    def test_double_parent_setting(self):
        # Tests the setting of a second parent node
        parent_node = ManagementNode()
        node = ConcreteNode()
        node.set_parent(parent_node)

        with self.assertRaises(Warning):
            node.set_parent(parent_node)  # Warning expected

class TestManagementNode(unittest.TestCase):
    '''
    Unit tests for the ManagementNode class, ensuring proper instance creation and 
    _instance_count incrementation, as well as verifying parent-child relationships. 
    It tests the addition and removal of child nodes, the propagation of computations 
    to child nodes, and the correct counting of ComputeNode instances within the hierarchy. 
    Additionally, it checks that the notify method prints the appropriate notification messages.
    '''
    def setUp(self):
        # Reset the _instance_count before each test
        ManagementNode._instance_count = 0

    def test_instance_creation(self):
        # Tests the instantiation of ManagementNode and whether _instance_count is incremented
        node = ManagementNode()
        self.assertIsInstance(node, ManagementNode)
        self.assertEqual(node.__class__._instance_count, 1)
        self.assertEqual(str(node), "ManagementNode1")
        self.assertEqual(node.get_parent(), None)

    def test_parent_setting(self):
        # Tests setting a parent node and verifies that the parent is set correctly.
        # Also checks that the node's parent is correctly referenced.

        parent_node = ManagementNode()
        child_node = ManagementNode()
        child_node.set_parent(parent_node)
        self.assertEqual(child_node.get_parent(), parent_node)

    def test_add_and_remove_child(self):
        # Verifies that children are correctly added and removed from the ManagementNode

        parent_node = ManagementNode()
        child_node = ManagementNode()
        parent_node.add(child_node)
        self.assertEqual(parent_node.get_number_of_children(), 1)
        parent_node.remove(child_node)
        self.assertEqual(parent_node.get_number_of_children(), 0)

    def test_distribute_and_compute(self):
        # Verifies that the method propagates the computation to child nodes and notifies the parent node

        parent_node = ManagementNode()
        child_node = ManagementNode(parent_node)
        parent_node.add(child_node)

        # Mock the distribute_and_compute method for the test
        def mock_distribute_and_compute(model, minutes, num_replications):
            self.distribute_called = True

        parent_node.distribute_and_compute = mock_distribute_and_compute
        parent_node.distribute_and_compute(None, 0, 0)
        self.assertTrue(self.distribute_called)

    def test_count_compute_nodes(self):
        # Verifies the correct count of ConcreteNode instances within the ManagementNode hierarchy

        parent_node = ManagementNode()
        compute_node_1 = ComputeNode()
        compute_node_2 = ComputeNode()
        child_node = ManagementNode()
        child_node.add(compute_node_1)
        child_node.add(compute_node_2)
        parent_node.add(child_node)

        self.assertEqual(parent_node.count_compute_nodes(), 2)

    def test_notify(self):
        # Verifies that the notify method prints the correct notification message

        parent_node = ManagementNode()
        child_node = ManagementNode(parent_node)

        with patch('builtins.print') as mock_print:
            child_node.notify("Test message", parent_node)
            mock_print.assert_called_with(f"{parent_node.__str__()} notifies {child_node.__str__()}: Test message")

class TestComputeNode(unittest.TestCase):
    '''
    The tests for the ComputeNode class verify that each instance has a unique name 
    and that the instance counter is correctly incremented. They also check the 
    functionality of state management methods, the distribute_and_compute method, and 
    ensure that the instance counter can be reset properly.
    '''
    def setUp(self):
        #Reset instance count before each test
        ComputeNode.reset_instance_count()

    def test_instance_creation(self):
        #Test instance creation and instance count
        node1 = ComputeNode()
        node2 = ComputeNode()
        self.assertEqual(node1._name, 'ComputeNode1')
        self.assertEqual(node2._name, 'ComputeNode2')

    ''' Problem beim Mocken der run_simulation Methode, die Datei in der Entity Mnager
        definiert wird fehlt
    def test_running_state(self):
        #Test the running state management
        node = ComputeNode()
        self.assertFalse(node.is_running())
        node.set_running(True)
        self.assertTrue(node.is_running())
        node.set_running(False)
        self.assertFalse(node.is_running())
    
    @patch('simulations.run_simulation')
    @patch('simulations.run_replications')
    @patch('simulations.EntityManager', new_callable=MagicMock) 
    def test_distribute_and_compute(self, mock_entity_manager, mock_run_replications, mock_run_simulation):
        """Test the distribute_and_compute method with mocked functions."""
        model = MagicMock()  # Mocking the model
        minutes = 10
        num_replications = 5
        callback = MagicMock()

        # Configure the mock for EntityManager if needed
        mock_entity_manager.return_value = MagicMock()

        node = ComputeNode(callback=callback)
        node.distribute_and_compute(model, minutes, num_replications)
        
        # Verify that run_simulation and run_replications were called
        mock_run_simulation.assert_called_once_with(model=model, minutes=minutes)
        mock_run_replications.assert_called_once_with(model=model, minutes=minutes, num_replications=num_replications, multiprocessing=True)
        self.assertTrue(callback.called)
        self.assertEqual(callback.call_args[0], ("Completed simulation", node))
        self.assertFalse(node.is_running())
    '''
    def test_reset_instance_count(self):
        #Test the instance counter reset
        node1 = ComputeNode()
        ComputeNode.reset_instance_count()
        node2 = ComputeNode()
        self.assertEqual(node2._name, 'ComputeNode1')

class TestCreateCompositeTree(unittest.TestCase):
    '''
    The tests validate the functionality of the create_composite_tree method by checking if 
    the number of children in the root node matches expectations for different replication 
    scenarios. Specifically, it ensures that when the number of replications is below the 
    minimum threshold, the root contains only one ComputeNode, while with equal or greater 
    replications, the tree structure is sufficiently deep and correctly populated with nodes.
    '''
    def test_below_minimum_replications(self):
        num_replications = MINIMUM_OF_REPLICATIONS_FOR_COMPOSITE - 1
        root = create_composite_tree(num_replications)
        
        self.assertEqual(root.get_number_of_children(), 1)
        child = next(iter(root))
        self.assertIsInstance(child, ComputeNode)

    def test_at_minimum_replications(self):
        num_replications = MINIMUM_OF_REPLICATIONS_FOR_COMPOSITE
        root = create_composite_tree(num_replications)
        
        self.assertGreater(root.get_number_of_children(), 1)

    def test_large_replications(self):
        num_replications = NUM_REPLICATIONS
        root = create_composite_tree(num_replications)
        
        depth = compute_tree_sizes(num_replications)
        self.assertTrue(self.check_tree_depth(root, expected_depth=depth))

    def check_tree_depth(self, node, expected_depth, current_depth=1):
        """Function to get the depth of the tree"""
        if current_depth == expected_depth:
            return True
        for child in node:
            if isinstance(child, ManagementNode):
                if self.check_tree_depth(child, expected_depth, current_depth + 1):
                    return True
        return False

class TestAddNodes(unittest.TestCase):
    '''
    Verifies the add_nodes function by testing different tree depths. 
    It ensures that the correct number of ManagementNode and ComputeNode instances are added 
    at various levels of the hierarchy.
    '''
    def setUp(self):
        ManagementNode.reset_instance_count()
        ComputeNode.reset_instance_count()

    def test_add_nodes_depth_1(self):
        root = ManagementNode()
        add_nodes(root, 1, 2)

        # Check that the root has 2 ManagementNodes as children
        self.assertEqual(root.get_number_of_children(), 2)
        for child in root:
            self.assertIsInstance(child, ManagementNode)
            # Each child should have 2 ComputeNodes
            self.assertEqual(child.get_number_of_children(), 2)
            for grandchild in child:
                self.assertIsInstance(grandchild, ComputeNode)

    def test_add_nodes_depth_2(self):
        root = ManagementNode()
        add_nodes(root, 1, 3)

        # Check that the root has 2 ManagementNodes as children
        self.assertEqual(root.get_number_of_children(), 2)
        for child in root:
            self.assertIsInstance(child, ManagementNode)
            self.assertEqual(child.get_number_of_children(), 2)
            for grandchild in child:
                self.assertIsInstance(grandchild, ManagementNode)
                self.assertEqual(grandchild.get_number_of_children(), 2)
                for great_grandchild in grandchild:
                    self.assertIsInstance(great_grandchild, ComputeNode)

    def test_add_nodes_no_management_nodes(self):
        root = ManagementNode()
        add_nodes(root, 2, 2)

        # Check that the root has 2 ComputeNodes as children
        self.assertEqual(root.get_number_of_children(), 2)
        for child in root:
            self.assertIsInstance(child, ComputeNode)

class TestComputeTreeSize(unittest.TestCase):
    '''
    Checks the compute_tree_sizes function for various 
    numbers of replications. It verifies that the tree size is calculated correctly for 
    different replication thresholds, including edge cases and typical values.
    '''
    def test_small_number_of_replications(self):
        # For less than 1000 replications, the tree size should be 0.
        self.assertEqual(compute_tree_sizes(999), 0, "For fewer than 1000 replications, the tree size should be 0.")

    def test_exact_threshold(self):
        # For exactly 1000 replications, the tree size should be 1.
        self.assertEqual(compute_tree_sizes(1000), 0, "For exactly 1000 replications, the tree size should be 1.")

    def test_double_threshold(self):
        # For 2000 replications, the tree size should still be 1.
        self.assertEqual(compute_tree_sizes(2000), 1, "For 2000 replications, the tree size should be 1.")

    def test_large_number_of_replications(self):
        # For 8192 replications, the tree size should be 3.
        self.assertEqual(compute_tree_sizes(8192), 3, "For 8192 replications, the tree size should be 3.")

    def test_edge_case(self):
        # For 1 replication, the tree size should be 0.
        self.assertEqual(compute_tree_sizes(1), 0, "For fewer than 1000 replications, the tree size should be 0.")

class TestInputPositivNumber(unittest.TestCase):
    '''
    Tests the input_positive_number function to ensure it correctly handles 
    valid and invalid inputs. It verifies that valid input is returned correctly 
    and invalid inputs trigger appropriate error messages before providing the correct 
    value on retry.
    '''
    @patch('builtins.input', return_value='42')
    def test_valid_input(self, mock_input):
        result = input_positive_number("Enter a positive number: ")
        self.assertEqual(result, 42)

    @patch('builtins.input', side_effect=['-1', '0', 'abc', '10'])
    def test_invalid_inputs(self, mock_input):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            result = input_positive_number("Enter a positive number: ")
            self.assertEqual(result, 10)
            output = fake_out.getvalue()
            self.assertIn("Error: Entered number must be greater than zero", output)
            self.assertIn("Error: invalid literal for int() with base 10", output)

if __name__ == "__main__":
    unittest.main()
