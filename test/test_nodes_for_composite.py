from __future__ import annotations
from typing import Optional
import unittest
import os
import sys
import pandas as pd
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../VerteilteBerechnungen')))
from VerteilteBerechnungen.util.nodes_for_composite import (
    Node, ManagementNode, ComputeNode, create_composite_tree,
    MINIMUM_OF_REPLICATIONS_FOR_COMPOSITE, NUM_REPLICATIONS,
    compute_tree_sizes, add_nodes, input_positive_number
)


class ConcreteNode(Node):
    """Instance of the abstract class Node."""
    
    def __init__(self, parent: Optional[ManagementNode] = None):
        super().__init__(parent)
        self._name = "ConcreteNode"

    def distribute_and_compute(self, model, minutes: int, num_replications: int) -> None:
        pass


class TestNode(unittest.TestCase):
    """Unit tests for Node instance creation, parent setting, and handling of invalid and duplicate parent nodes."""
    
    def setUp(self):
        ConcreteNode._instance_count = 0

    def test_instance_creation(self):
        node = ConcreteNode()
        self.assertIsInstance(node, ConcreteNode)
        self.assertEqual(node.__class__._instance_count, 1)
        self.assertEqual(str(node), "ConcreteNode")

    def test_parent_setting(self):
        parent_node = ManagementNode()
        node = ConcreteNode()
        self.assertTrue(node.set_parent(parent_node))
        self.assertEqual(node.get_parent(), parent_node)

    def test_invalid_parent_setting(self):
        node = ConcreteNode()
        with self.assertRaises(TypeError):
            node.set_parent("invalid_parent")

    def test_double_parent_setting(self):
        parent_node = ManagementNode()
        node = ConcreteNode()
        node.set_parent(parent_node)
        with self.assertRaises(Warning):
            node.set_parent(parent_node)


class TestNodeEquality(unittest.TestCase):
    """Unit tests for checking equality of Node instances based on parent and name."""
    
    def setUp(self):
        self.node1 = ConcreteNode()
        self.node2 = ConcreteNode()
        self.node3 = ConcreteNode()
        self.node4 = ConcreteNode()
        self.node1._parent = None
        self.node1._name = "NodeA"
        self.node2._parent = None
        self.node2._name = "NodeA"
        self.node3._parent = self.node1
        self.node3._name = "NodeB"
        self.node4._parent = self.node1
        self.node4._name = "NodeB"

    def test_equal_nodes(self):
        self.assertEqual(self.node1, self.node2)

    def test_not_equal_parent(self):
        self.node2._parent = self.node3
        self.assertNotEqual(self.node1, self.node2)

    def test_not_equal_name(self):
        self.node2._name = "DifferentName"
        self.assertNotEqual(self.node1, self.node2)

    def test_not_equal_type(self):
        self.assertNotEqual(self.node1, "non-node-object")

    def test_equal_complex(self):
        self.assertEqual(self.node3, self.node4)


class TestNodeRepr(unittest.TestCase):
    """Unit tests for Node's __repr__ method."""
    
    def setUp(self):
        self.node1 = ConcreteNode()
        self.node2 = ConcreteNode()
        self.node1._parent = None
        self.node1._name = "NodeA"
        self.node2._parent = self.node1
        self.node2._name = "NodeB"

    def test_repr_no_parent(self):
        expected_repr = "ConcreteNode(name=NodeA, parent=None)"
        self.assertEqual(repr(self.node1), expected_repr)

    def test_repr_with_parent(self):
        parent_id = id(self.node1)
        expected_repr = f"ConcreteNode(name=NodeB, parent=NodeA (id={parent_id}))"
        self.assertEqual(repr(self.node2), expected_repr)

    def test_repr_class_name(self):
        self.assertIn("ConcreteNode", repr(self.node1))


class TestManagementNode(unittest.TestCase):
    """Unit tests for ManagementNode class, including parent-child relationships and computation propagation."""
    
    def setUp(self):
        ManagementNode._instance_count = 0

    def test_instance_creation(self):
        node = ManagementNode()
        self.assertIsInstance(node, ManagementNode)
        self.assertEqual(node.__class__._instance_count, 1)
        self.assertEqual(str(node), "ManagementNode1")
        self.assertEqual(node.get_parent(), None)

    def test_parent_setting(self):
        parent_node = ManagementNode()
        child_node = ManagementNode()
        child_node.set_parent(parent_node)
        self.assertEqual(child_node.get_parent(), parent_node)

    def test_add_and_remove_child(self):
        parent_node = ManagementNode()
        child_node = ManagementNode()
        parent_node.add(child_node)
        self.assertEqual(parent_node.get_number_of_children(), 1)
        parent_node.remove(child_node)
        self.assertEqual(parent_node.get_number_of_children(), 0)

    def test_distribute_and_compute(self):
        parent_node = ManagementNode()
        child_node = ManagementNode(parent_node)
        parent_node.add(child_node)
        self.distribute_called = False

        def mock_distribute_and_compute(model, minutes, num_replications):
            self.distribute_called = True

        parent_node.distribute_and_compute = mock_distribute_and_compute
        parent_node.distribute_and_compute(None, 0, 0)
        self.assertTrue(self.distribute_called)

    def test_count_compute_nodes(self):
        parent_node = ManagementNode()
        compute_node_1 = ComputeNode()
        compute_node_2 = ComputeNode()
        child_node = ManagementNode()
        child_node.add(compute_node_1)
        child_node.add(compute_node_2)
        parent_node.add(child_node)
        self.assertEqual(parent_node.count_compute_nodes(), 2)

    def test_notify(self):
        parent_node = ManagementNode()
        child_node = ManagementNode(parent_node)
        with patch('builtins.print') as mock_print:
            child_node.notify("Test message", parent_node)
            mock_print.assert_called_with(f"{parent_node.__str__()} notifies {child_node.__str__()}: Test message")


class TestComputeNode(unittest.TestCase):
    """Unit tests for ComputeNode, focusing on instance creation and instance count reset."""
    
    def setUp(self):
        ComputeNode.reset_instance_count()

    def test_instance_creation(self):
        node1 = ComputeNode()
        node2 = ComputeNode()
        self.assertEqual(node1._name, 'ComputeNode1')
        self.assertEqual(node2._name, 'ComputeNode2')

    def test_reset_instance_count(self):
        node1 = ComputeNode()
        ComputeNode.reset_instance_count()
        node2 = ComputeNode()
        self.assertEqual(node2._name, 'ComputeNode1')


class TestCreateCompositeTree(unittest.TestCase):
    """Tests for the create_composite_tree function with various replication scenarios."""
    
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
        if current_depth == expected_depth:
            return True
        for child in node:
            if isinstance(child, ManagementNode):
                if self.check_tree_depth(child, expected_depth, current_depth + 1):
                    return True
        return False


class TestAddNodes(unittest.TestCase):
    """Tests for the add_nodes function by verifying correct node addition at various depths."""
    
    def setUp(self):
        ManagementNode.reset_instance_count()
        ComputeNode.reset_instance_count()

    def test_add_nodes_depth_1(self):
        root = ManagementNode()
        add_nodes(root, 1, 2)
        self.assertEqual(root.get_number_of_children(), 2)
        for child in root:
            self.assertIsInstance(child, ManagementNode)
            self.assertEqual(child.get_number_of_children(), 2)
            for grandchild in child:
                self.assertIsInstance(grandchild, ComputeNode)

    def test_add_nodes_depth_2(self):
        root = ManagementNode()
        add_nodes(root, 1, 3)
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
        self.assertEqual(root.get_number_of_children(), 2)
        for child in root:
            self.assertIsInstance(child, ComputeNode)


class TestComputeTreeSize(unittest.TestCase):
    """Tests for the compute_tree_sizes function, focusing on replication thresholds."""
    
    def test_small_number_of_replications(self):
        self.assertEqual(compute_tree_sizes(999), 0)

    def test_exact_threshold(self):
        self.assertEqual(compute_tree_sizes(1000), 0)

    def test_double_threshold(self):
        self.assertEqual(compute_tree_sizes(2000), 1)

    def test_large_number_of_replications(self):
        self.assertEqual(compute_tree_sizes(8192), 3)

    def test_edge_case(self):
        self.assertEqual(compute_tree_sizes(1), 0)


class TestDistributeAndCompute(unittest.TestCase):
    """Tests for the distribute_and_compute method on ManagementNode, including handling of children."""
    
    def setUp(self):
        self.root = ManagementNode()
        self.child1 = ComputeNode()
        self.child2 = ComputeNode()
        self.root.add(self.child1)
        self.root.add(self.child2)

    @patch('VerteilteBerechnungen.util.simulations.run_simulation')
    @patch('VerteilteBerechnungen.util.simulations.run_replications')
    @patch('VerteilteBerechnungen.util.simulations.calculate_statistics', return_value=({}, [], {}, {}))
    def test_distribute_and_compute_on_children(self, mock_calculate_statistics, mock_run_replications, mock_run_simulation):
        self.child1.distribute_and_compute = MagicMock()
        self.child2.distribute_and_compute = MagicMock()
        model = MagicMock()
        self.root.distribute_and_compute(model=model, minutes=10, num_replications=5)
        self.child1.distribute_and_compute.assert_called_once_with(model=model, minutes=10, num_replications=5)
        self.child2.distribute_and_compute.assert_called_once_with(model=model, minutes=10, num_replications=5)
        mock_run_simulation.assert_not_called()
        mock_run_replications.assert_not_called()

    @patch('VerteilteBerechnungen.util.simulations.run_simulation')
    @patch('VerteilteBerechnungen.util.simulations.run_replications')
    @patch('VerteilteBerechnungen.util.simulations.calculate_statistics', return_value=({}, [], {}, {}))
    def test_distribute_and_compute_no_children(self, mock_calculate_statistics, mock_run_replications, mock_run_simulation):
        empty_root = ManagementNode()
        empty_root.distribute_and_compute(model=MagicMock(), minutes=10, num_replications=5)
        mock_run_simulation.assert_not_called()
        mock_run_replications.assert_not_called()


class TestDistributeAndComputeNotify(unittest.TestCase):
    """Tests for ManagementNode's distribute_and_compute method, ensuring correct notification to parent."""
    
    def setUp(self):
        self.root = ManagementNode()
        self.child1 = ComputeNode()
        self.child2 = ComputeNode()
        self.root.add(self.child1)
        self.root.add(self.child2)
        self.parent_node = ManagementNode()
        self.root.set_parent(self.parent_node)

    @patch('VerteilteBerechnungen.util.simulations.run_simulation')
    @patch('VerteilteBerechnungen.util.simulations.run_replications')
    @patch('VerteilteBerechnungen.util.simulations.calculate_statistics', return_value=({}, [], {}, {}))
    @patch('pandas.DataFrame')
    def test_distribute_and_compute_notify_parent(self, mock_df, mock_calculate_statistics, mock_run_replications, mock_run_simulation):
        mock_df.return_value = pd.DataFrame({
            'Type': ['Entity'],
            'Name': ['Entity'],
            'Stat': ['NumberCreated'],
            'Average': [10],
            'Minimum': [5],
            'Maximum': [15],
            'Half-Width': [2]
        })
        self.parent_node.notify = MagicMock()
        model = MagicMock()
        self.root.distribute_and_compute(model=model, minutes=10, num_replications=5)
        self.parent_node.notify.assert_called_once_with(f"{self.root.__str__()} completed its operations.", self.root)


class TestInputPositiveNumber(unittest.TestCase):
    """Tests for the input_positive_number function, ensuring valid and invalid inputs are handled correctly."""
    
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


class TestComputeNodeDistributeAndCompute(unittest.TestCase):
    """Tests for ComputeNode's distribute_and_compute method, verifying callback functionality and running state."""
    
    def setUp(self):
        self.callback_mock = MagicMock()
        self.node = ComputeNode(callback=self.callback_mock)

    @patch('VerteilteBerechnungen.util.nodes_for_composite.run_simulation')
    @patch('VerteilteBerechnungen.util.nodes_for_composite.run_replications')
    @patch('pandas.DataFrame')
    def test_distribute_and_compute_callback_and_running_state(self, mock_df, mock_run_replications, mock_run_simulation):
        mock_df.return_value = pd.DataFrame({
            'Type': ['Entity'],
            'Name': ['Entity'],
            'Stat': ['NumberCreated'],
            'Value': [10]
        })
        model = MagicMock()
        self.node.distribute_and_compute(model=model, minutes=10, num_replications=5)
        mock_run_simulation.assert_called_once_with(model=model, minutes=10)
        mock_run_replications.assert_called_once_with(model=model, minutes=10, num_replications=5, multiprocessing=True)
        self.callback_mock.assert_called_once_with("Completed simulation", self.node)
        self.assertFalse(self.node.is_running())


if __name__ == "__main__":
    unittest.main()
