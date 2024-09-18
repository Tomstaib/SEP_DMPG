from __future__ import annotations
from typing import Optional
from unittest.mock import patch, MagicMock, call
from watchdog.events import FileSystemEvent
from graphviz import Digraph
import os
import time
import unittest
from composite_tree import CompositeTree
from util.nodes_for_composite import ManagementNode, Node, ComputeNode

sys.path.append('/app/Verteilung/util')

class TestCompositeTree(unittest.TestCase):
    '''
    The code uses patch to replace specific components in the composite_tree module with mock objects
    during testing. This includes mocking the input_positive_number and confirm_input functions to 
    simulate user input, and replacing destroy_composite_tree, ComputeNode, and ManagementNode with 
    mocks to track their usage and interactions. These mocks help ensure that the test can verify 
    behavior without relying on actual implementations or user inputs.
    '''
    def test_create_custom_composite_tree(self):
        with patch('composite_tree.input_positive_number', side_effect=[3, 2]) as mock_input, \
             patch('composite_tree.CompositeTree.confirm_input', side_effect=[True, False]) as mock_confirm_input, \
             patch('composite_tree.CompositeTree.destroy_composite_tree') as mock_destroy_tree, \
             patch('composite_tree.ComputeNode', return_value=MagicMock()) as mock_compute_node, \
             patch('composite_tree.ManagementNode') as mock_management_node:
            
            CompositeTree.create_custom_composite_tree()

            mock_input.assert_any_call("Please enter how many children a Management Node should have")
            mock_input.assert_any_call("Please enter the depth of the tree")

            mock_confirm_input.assert_any_call("Do you want to proceed with these settings? [y/n]:\nDepth of the tree: 2\nNumber of children per parent: 3\nTotal number of compute Nodes: 9")

            mock_destroy_tree.assert_called_once()

            # verify the number of created nodes
            expected_compute_nodes = 3**2  # Anzahl der ComputeNodes in einem Baum der Tiefe 2 und 3 Kinder pro Knoten
            self.assertEqual(mock_compute_node.call_count, expected_compute_nodes)

            # verify the order of node creation
            management_node_calls = [call(parent=MagicMock())] * (expected_compute_nodes - 1)
            compute_node_calls = [call()] * (expected_compute_nodes - 3)
            expected_calls = management_node_calls + compute_node_calls


    def test_get_root(self):
        with patch('composite_tree.input_positive_number', side_effect=[3, 2]) as mock_input, \
             patch('composite_tree.CompositeTree.confirm_input', side_effect=[True, False]) as mock_confirm_input:
            
            CompositeTree.create_custom_composite_tree()

        root = CompositeTree.get_root()
        self.assertIsInstance(root, ManagementNode)

    def test_destroy_composite_tree(self):
        with patch('composite_tree.input_positive_number', side_effect=[3, 2]) as mock_input, \
             patch('composite_tree.CompositeTree.confirm_input', side_effect=[True, False]) as mock_confirm_input:
            
            CompositeTree.create_custom_composite_tree()
            initial_root = CompositeTree.get_root()

        CompositeTree.destroy_composite_tree()
        new_root = CompositeTree.get_root()
        
        self.assertIsNot(initial_root, new_root, "Der Baum sollte zurückgesetzt werden.")
        self.assertIsInstance(new_root, ManagementNode, "Der neue Wurzelknoten sollte vom Typ ManagementNode sein.")
        self.assertEqual(new_root.get_number_of_children(), 0, "Der neue Baum sollte keine Kinder haben.")

    def test_get_replications_per_node(self):

        CompositeTree.set_replications_per_node(5)
        self.assertEqual(CompositeTree.get_replications_per_node(),5)

        CompositeTree.set_replications_per_node(10)
        self.assertEqual(CompositeTree.get_replications_per_node(),10)

        CompositeTree.destroy_composite_tree()
        self.assertEqual(CompositeTree.get_replications_per_node(),0)
    
    def test_set_replications_per_node(self):
        CompositeTree.set_replications_per_node(5)
        self.assertEqual(CompositeTree.get_replications_per_node(), 5)

        CompositeTree.set_replications_per_node(10)
        self.assertEqual(CompositeTree.get_replications_per_node(), 10)

        CompositeTree.set_replications_per_node(0)
        self.assertEqual(CompositeTree.get_replications_per_node(), 0)

        with self.assertRaises(ValueError):
            CompositeTree.set_replications_per_node(-1)
    
    def tearDown(self):
        CompositeTree.destroy_composite_tree()
    
class TestFindNodeByName(unittest.TestCase):
    '''
    Verifies the CompositeTree._find_node_by_name method by testing node retrieval for 
    both ComputeNode and ManagementNode types, as well as handling cases where the node 
    name does not exist. It ensures that the method returns the correct node when found 
    and None when the name does not match any existing node.
    '''
    def setUp(self):
        with patch('composite_tree.input_positive_number', side_effect=[3, 2]) as mock_input, \
             patch('composite_tree.CompositeTree.confirm_input', side_effect=[True, False]) as mock_confirm_input:
            
            CompositeTree.create_custom_composite_tree()
            
    def test_find_node_by_name_ComputeNode(self):
        
        node = CompositeTree._find_node_by_name('ComputeNode1')
        self.assertIsNotNone(node)
        self.assertEqual(str(node), 'ComputeNode1')

    def test_find_node_by_name_ManagementNode(self):
        
        node = CompositeTree._find_node_by_name('ManagementNode1')
        self.assertIsNotNone(node)
        self.assertEqual(str(node), 'ManagementNode1')

    def test_find_node_by_name_failed(self):

        node = CompositeTree._find_node_by_name('WrongName22')
        self.assertIsNone(node)

    def tearDown(self):
        CompositeTree.destroy_composite_tree()

class TestHasRunningComputeNode(unittest.TestCase):
    '''
    Tests the CompositeTree._has_running_compute_node method for detecting running 
    ComputeNode instances. It checks whether the method correctly identifies nodes 
    with a running state and handles cases with no running nodes or empty node lists.
    '''
    def setUp(self):
        self.node1 = MagicMock()
        self.node2 = MagicMock()
        self.node3 = MagicMock()

        self.node1.is_running.return_value = True
        self.node2.is_running.return_value = False
        self.node3.is_running.return_value = False

        self.node1.__class__ = ComputeNode
        self.node2.__class__ = ComputeNode
        self.node3.__class__ = ComputeNode

        self.management_node1 = MagicMock()
        self.management_node2 = MagicMock()

        self.management_node1.__class__ = ManagementNode
        self.management_node2.__class__ = ManagementNode

        self.management_node1.__iter__.return_value = [self.node2, self.node3]
        self.management_node2.__iter__.return_value = [self.node1]

        self.root_node = self.management_node2

    def test_has_running_compute_node_found(self):
        result = CompositeTree._has_running_compute_node(self.root_node)
        self.assertTrue(result)

    def test_has_running_compute_node_not_found(self):
        self.node1.is_running.return_value = False
        result = CompositeTree._has_running_compute_node(self.root_node)
        self.assertFalse(result)

    def test_has_running_compute_node_empty(self):
        self.management_node1.__iter__.return_value = []
        result = CompositeTree._has_running_compute_node(self.management_node1)
        self.assertFalse(result)

class TestCountComputeNodes(unittest.TestCase):
    '''
    Tests the CompositeTree.count_compute_nodes method to ensure it accurately 
    counts the number of ComputeNode instances. It verifies counting in various 
    scenarios, including nested ManagementNode structures and cases with no ComputeNode 
    instances
    '''
    def setUp(self):
        self.node1 = MagicMock()
        self.node2 = MagicMock()
        self.node3 = MagicMock()

        self.node1.__class__ = ComputeNode
        self.node2.__class__ = ComputeNode
        self.node3.__class__ = ComputeNode
        
        self.management_node1 = MagicMock()
        self.management_node2 = MagicMock()
        
        self.management_node1.__class__ = ManagementNode
        self.management_node2.__class__ = ManagementNode
        
        self.management_node1.__iter__.return_value = [self.node2, self.node3]
        self.management_node2.__iter__.return_value = [self.node1]
        
        self.root_node = self.management_node2
        
    def test_count_compute_nodes_sucessfull(self):
        # simple test for counting compute nodes
        count = CompositeTree.count_compute_nodes(self.root_node)
        self.assertEqual(count, 1)

    def test_count_compute_nodes_nested(self):
        # testing with nedted ManagementNodes
        self.management_node2.__iter__.return_value = [self.management_node1, self.node1]
        count = CompositeTree.count_compute_nodes(self.root_node)
        self.assertEqual(count, 3)

    def test_count_compute_nodes_no_nodes(self):
        # testing when 0 compute nodes are given
        self.management_node2.__iter__.return_value = []
        count = CompositeTree.count_compute_nodes(self.root_node)
        self.assertEqual(count, 0)

class TestNewJobFileHandler(unittest.TestCase):
    '''
    Ensures that the on_created method of NewJobFileHandler correctly 
    invokes _process_job_file with the file path from a mocked FileSystemEvent
    '''
    @patch.object(CompositeTree, '_process_job_file')
    def test_on_created(self, mock_process_job_file):
        # Creating an instance of NewJobFileHandler and a mock FileSystemEvent
        handler = CompositeTree.NewJobFileHandler()
        event = FileSystemEvent(src_path='fake_path/job_file.txt')
        event.is_directory = False

        # Calling the on_created method with the mock event
        handler.on_created(event)

        # Verifing that _process_job_file was called with the correct file path
        mock_process_job_file.assert_called_once_with('fake_path/job_file.txt')

class TestCountNotRunningComputeNodes(unittest.TestCase):
    '''
    Verifies the functionality of counting ComputeNode instances that are not running 
    within a ManagementNode hierarchy. It includes tests for basic counting, nested nodes, 
    and scenarios with no nodes present
    '''
    def setUp(self):

        self.node1 = MagicMock()
        self.node2 = MagicMock()
        self.node3 = MagicMock()

        self.node1.__class__ = ComputeNode
        self.node2.__class__ = ComputeNode
        self.node3.__class__ = ComputeNode

        self.node1.is_running.return_value = False  # Not running
        self.node2.is_running.return_value = True   # running
        self.node3.is_running.return_value = False  # Not running

        self.management_node1 = MagicMock()
        self.management_node2 = MagicMock()

        self.management_node1.__class__ = ManagementNode
        self.management_node2.__class__ = ManagementNode

        self.management_node1.__iter__.return_value = [self.node2, self.node3]
        self.management_node2.__iter__.return_value = [self.node1]

        self.root_node = self.management_node2

    def test_count_not_running_compute_nodes(self):
        # counting not running computenodes
        count = CompositeTree.count_not_running_compute_nodes(self.root_node)
        self.assertEqual(count, 1)

    def test_count_not_running_compute_nodes_nested(self):
        # test with nested nodes
        self.management_node2.__iter__.return_value = [self.management_node1, self.node1]
        count = CompositeTree.count_not_running_compute_nodes(self.root_node)
        self.assertEqual(count, 2)

    def test_count_not_running_compute_nodes_no_nodes(self):
        # testing when 0 nodes are given
        self.management_node2.__iter__.return_value = []
        count = CompositeTree.count_not_running_compute_nodes(self.root_node)
        self.assertEqual(count, 0)

class TestHandleNodeCallback(unittest.TestCase):
    '''
    Validates the behavior of the handle_node_callback method in CompositeTree for different
    scenarios. It checks successful handling when a ComputeNode is found and properly flagged,
    handles cases where nodes are not found or are not ComputeNode instances, and ensures that
    exceptions are caught and reported correctly. Each test includes appropriate mock configurations 
    and verifies output and method calls
    '''
    def setUp(self):

        self.compute_node = MagicMock()
        self.compute_node.__class__ = ComputeNode

        # Patching the "find_node_by_name" method
        patcher = patch('composite_tree.CompositeTree._find_node_by_name', return_value=self.compute_node)
        self.mock_find_node_by_name = patcher.start()
        self.addCleanup(patcher.stop)

    def test_handle_node_callback_success(self):
        # Find node and set flag on false
        CompositeTree.handle_node_callback("node1")

        self.mock_find_node_by_name.assert_called_once_with("node1")
        self.compute_node.set_running.assert_called_once_with(False)

    def test_handle_node_callback_node_not_found(self):
        # Node not found
        self.mock_find_node_by_name.return_value = None

        with patch('builtins.print') as mocked_print:
            CompositeTree.handle_node_callback("unknown_node")
            mocked_print.assert_called_with("No node with name 'unknown_node' found.")

        self.compute_node.set_running.assert_not_called()

    def test_handle_node_callback_not_compute_node(self):
        # Found node is not a compute node
        self.mock_find_node_by_name.return_value = MagicMock()

        with patch('builtins.print') as mocked_print:
            CompositeTree.handle_node_callback("invalid_node")
            mocked_print.assert_called_with("Node 'invalid_node' is not a ComputeNode.")

        self.compute_node.set_running.assert_not_called()

    def test_handle_node_callback_exception(self):
        # Testing to throw an exception
        self.mock_find_node_by_name.side_effect = Exception("Unexpected error")

        with patch('builtins.print') as mocked_print:
            CompositeTree.handle_node_callback("node1")
            mocked_print.assert_called_with("Error handling callback for node 'node1': Unexpected error")

        self.compute_node.set_running.assert_not_called()




'''
class TestVisualizeTree(unittest.TestCase):

    @patch('graphviz.Digraph')
    def test_visualize_tree(self, mock_digraph):
        mock_dot_instance = mock_digraph.return_value
        mock_dot_instance.render.return_value = 'CompositeTree.gv'

        CompositeTree.visualize_tree()

        mock_dot_instance.render.assert_called_with('CompositeTree.gv', view=True)

        self.assertTrue(os.path.exists('CompositeTree.gv'))
        

    def tearDown(self):
        if os.path.exists('CompositeTree.gv'):
            os.remove('CompositeTree.gv')
'''


if __name__ == '__main__':
    unittest.main()
