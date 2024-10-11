import os
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from graphviz import Digraph

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Verteilung'))
)
from Verteilung.composite_tree import (
    CompositeTree,
    ComputeNode,
    ManagementNode,
    main,
    Node,
)
from Verteilung.util.flask.nodes_for_composite import input_positive_number


class TestCompositeTree(unittest.TestCase):

    def setUp(self):
        CompositeTree.destroy_composite_tree()

    @patch('Verteilung.composite_tree.CompositeTree.confirm_input')
    @patch('Verteilung.composite_tree.ManagementNode.add')
    def test_add_node(self, mock_add, mock_confirm):
        """
        Tests adding a node to the CompositeTree structure.
        """
        node = MagicMock(spec=Node)
        CompositeTree._CompositeTree__add_node(node)

        mock_add.assert_called_once_with(node)

    @patch('Verteilung.composite_tree.CompositeTree.confirm_input')
    @patch('Verteilung.composite_tree.ManagementNode.remove')
    def test_remove_node(self, mock_remove, mock_confirm):
        """
        Tests removing a node from the CompositeTree structure.
        """
        node = MagicMock(spec=Node)
        CompositeTree._CompositeTree__remove_node(node)

        mock_remove.assert_called_once_with(node)

    def test_get_root(self):
        """
        Tests whether the root node is correctly returned.
        """
        root = CompositeTree.get_root()
        self.assertIsInstance(root, ManagementNode,
                              "Root should be a ManagementNode instance.")

    def test_get_replications_per_node(self):
        """
        Tests whether the number of replications per node is correctly returned.
        """
        CompositeTree.set_replications_per_node(5)
        self.assertEqual(CompositeTree.get_replications_per_node(), 5,
                         "Replications per node should be 5.")

    def test_set_replications_per_node(self):
        """
        Tests setting the replications per node, including checking for negative values.
        """
        CompositeTree.set_replications_per_node(10)
        self.assertEqual(CompositeTree.get_replications_per_node(), 10,
                         "Replications per node should be 10.")

        with self.assertRaises(ValueError):
            CompositeTree.set_replications_per_node(-1)


class TestCompositeTreeAddNode(unittest.TestCase):

    @patch('Verteilung.composite_tree.ManagementNode.add')
    def test_add_node_with_none_parent(self, mock_add):
        """
        Tests adding a node when no parent node is specified.
        """
        node = MagicMock(spec=Node)

        CompositeTree._CompositeTree__add_node(node)

        root_node = CompositeTree.get_root()
        mock_add.assert_called_once_with(node)
        self.assertEqual(mock_add.call_args[0][0], node)

    def test_add_node_with_parent(self):
        """
        Tests adding a node when a parent node is specified.
        """
        parent_node = MagicMock(spec=ManagementNode)
        node = MagicMock(spec=Node)

        parent_node.add = MagicMock()

        CompositeTree._CompositeTree__add_node(node, parent=parent_node)

        parent_node.add.assert_called_once_with(node)


class TestCompositeTreeRemoveNode(unittest.TestCase):

    def setUp(self):
        patcher_root = patch('Verteilung.composite_tree.CompositeTree._CompositeTree__root',
                             new_callable=MagicMock)
        self.mock_root = patcher_root.start()
        self.addCleanup(patcher_root.stop)

    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__remove_node')
    def test_remove_node_with_none_parent(self, mock_remove_node):
        """
        Tests removing a node when no parent node is specified.
        """
        node = MagicMock(spec=Node)

        CompositeTree._CompositeTree__remove_node(node)

        self.mock_root.remove.assert_called_once_with(node)

    def test_remove_node_with_parent(self):
        """
        Tests removing a node when a parent node is specified.
        """
        parent_node = MagicMock(spec=ManagementNode)
        node = MagicMock(spec=Node)

        parent_node.remove = MagicMock()

        CompositeTree._CompositeTree__remove_node(node, parent=parent_node)

        parent_node.remove.assert_called_once_with(node)


class TestCompositeTreeCreateCustomTree(unittest.TestCase):

    def setUp(self):
        CompositeTree.destroy_composite_tree()

    @patch('Verteilung.composite_tree.CompositeTree.confirm_input', return_value=True)
    @patch('Verteilung.composite_tree.input_positive_number', side_effect=[2, 3])
    @patch('Verteilung.composite_tree.CompositeTree.destroy_composite_tree')
    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__build_composite_tree')
    def test_create_custom_composite_tree_success(
            self, mock_build_tree, mock_destroy_tree, mock_input, mock_confirm):
        """
        Tests the successful creation of a custom tree.
        """
        CompositeTree.create_custom_composite_tree()

        mock_input.assert_any_call(
            "Please enter how many children a Management Node should have")
        mock_input.assert_any_call("Please enter the depth of the tree")

        mock_confirm.assert_called_once_with(
            "Do you want to proceed with these settings? [y/n]:"
            "\nDepth of the tree: 3"
            "\nNumber of children per parent: 2"
            "\nTotal number of compute Nodes: 8"
        )

        mock_destroy_tree.assert_called_once()
        mock_build_tree.assert_called_once_with(
            [CompositeTree._CompositeTree__root], 3, 2)

    @patch('Verteilung.composite_tree.CompositeTree.confirm_input',
           side_effect=[False, False])
    @patch('Verteilung.composite_tree.input_positive_number', side_effect=[2, 3])
    def test_create_custom_composite_tree_exit(self, mock_input, mock_confirm):
        """
        Tests whether the tree creation is correctly aborted when the user rejects the input.
        """
        CompositeTree.create_custom_composite_tree()

        mock_input.assert_any_call(
            "Please enter how many children a Management Node should have")
        mock_input.assert_any_call("Please enter the depth of the tree")

        self.assertEqual(mock_confirm.call_count, 2)
        mock_confirm.assert_any_call(
            "Do you want to proceed with these settings? [y/n]:"
            "\nDepth of the tree: 3"
            "\nNumber of children per parent: 2"
            "\nTotal number of compute Nodes: 8"
        )
        mock_confirm.assert_any_call(
            "Do you want to create another composite tree? [y/n]: ")

    
class TestCompositeTreeIntegration(unittest.TestCase):

    def setUp(self):
        CompositeTree.destroy_composite_tree()

    @patch('Verteilung.composite_tree.ComputeNode')
    @patch('Verteilung.composite_tree.ManagementNode')
    @patch('Verteilung.composite_tree.CompositeTree.confirm_input',
           return_value=True)
    @patch('Verteilung.composite_tree.input_positive_number', side_effect=[3, 2])
    def test_create_custom_composite_tree(
            self, mock_input_positive_number, mock_confirm_input,
            mock_management_node, mock_compute_node):
        """
        Tests the integration of the tree structure by creating a custom CompositeTree structure.
        """
        CompositeTree.create_custom_composite_tree()

        expected_compute_nodes = 3 ** 2
        self.assertEqual(
            mock_compute_node.call_count,
            expected_compute_nodes,
            f"Expected {expected_compute_nodes} ComputeNodes to be created, "
            f"but got {mock_compute_node.call_count}."
        )

    @patch('Verteilung.composite_tree.CompositeTree._run_simulation',
           return_value=None)
    @patch('Verteilung.composite_tree.CompositeTree._create_additional_compute_nodes',
           return_value=None)
    @patch('Verteilung.composite_tree.CompositeTree.confirm_input',
           return_value=True)
    @patch('Verteilung.composite_tree.input_positive_number',
           side_effect=[10, 5])
    @patch('Verteilung.composite_tree.CompositeTree.count_not_running_compute_nodes',
           return_value=10)
    @patch('Verteilung.composite_tree.CompositeTree.count_compute_nodes',
           return_value=10)
    def test_start_simulation(
            self, mock_count_compute, mock_count_not_running,
            mock_input_positive_number, mock_confirm_input,
            mock_create_additional_nodes, mock_run_simulation):
        """
        Tests the start of the simulation, specifying the number of ComputeNodes and replications.
        """
        CompositeTree.start_simulation(
            10, 5, 'test_account', 'test_user', 'model_script.py', 60, 2)

        mock_run_simulation.assert_called_once_with(
            CompositeTree.get_root(),
            5,  # Number of replications per node
            2,  # CPUs per task
            'test_account',
            'test_user',
            'model_script.py',
            60,
            2
        )

    @patch('Verteilung.composite_tree.CompositeTree._process_job_file')
    def test_file_monitoring(self, mock_process_job_file):
        """
        Tests file monitoring and reaction to new files.
        """
        event = MagicMock()
        event.is_directory = False
        event.src_path = 'fake_path/job_file.txt'

        handler = CompositeTree.NewJobFileHandler()
        handler.on_created(event)

        mock_process_job_file.assert_called_once_with(
            'fake_path/job_file.txt')

    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name')
    def test_handle_node_callback(self, mock_find_node):
        """
        Tests the callback handling after a job completion to update the node status.
        """
        mock_compute_node = MagicMock(spec=ComputeNode)
        mock_find_node.return_value = mock_compute_node

        CompositeTree.handle_node_callback('ComputeNode1')

        mock_find_node.assert_called_once_with('ComputeNode1')
        mock_compute_node.set_running.assert_called_once_with(False)


class TestCompositeTreeErrorHandling(unittest.TestCase):

    @patch('Verteilung.composite_tree.input_positive_number',
           side_effect=Exception("Test Exception"))
    @patch('builtins.print')
    def test_create_custom_composite_tree_exception(
            self, mock_print, mock_input):
        """
        Tests whether the 'except' block in create_custom_composite_tree is reached when an exception occurs.
        """
        with patch('Verteilung.composite_tree.CompositeTree.confirm_input',
                   return_value=True):
            CompositeTree.create_custom_composite_tree()

        mock_print.assert_called_with("Error: Test Exception")


class TestCompositeTreeWithParams(unittest.TestCase):

    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__build_composite_tree')
    def test_create_custom_composite_tree_with_params_success(
            self, mock_build_tree):
        """
        Tests the successful creation of a custom tree with the specified parameters.
        """
        result = CompositeTree.create_custom_composite_tree_with_params(3, 2)

        mock_build_tree.assert_called_once_with(
            [CompositeTree.get_root()], 2, 3)
        self.assertEqual(
            result, CompositeTree.get_root(),
            "The returned root node should be __root."
        )

    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__build_composite_tree',
           side_effect=Exception("Test Exception"))
    @patch('builtins.print')
    def test_create_custom_composite_tree_with_params_exception(
            self, mock_print, mock_build_tree):
        """
        Tests whether the 'except' block in create_custom_composite_tree_with_params is reached when an exception occurs.
        """
        result = CompositeTree.create_custom_composite_tree_with_params(3, 2)

        mock_print.assert_any_call("Error: Test Exception")

        self.assertIsNone(
            result, "The return value should be None if an exception occurs."
        )

    def test_create_custom_composite_tree_with_invalid_params(self):
        """
        Tests whether no tree generation occurs with invalid parameters and a ValueError is raised.
        """
        with self.assertRaises(ValueError) as context1:
            CompositeTree.create_custom_composite_tree_with_params(-1, 2)
        self.assertEqual(
            str(context1.exception),
            "Number of children per parent must be a positive integer."
        )

        with self.assertRaises(ValueError) as context2:
            CompositeTree.create_custom_composite_tree_with_params(3, -2)
        self.assertEqual(
            str(context2.exception),
            "Depth of the tree must be a positive integer."
        )

        with self.assertRaises(ValueError) as context3:
            CompositeTree.create_custom_composite_tree_with_params("three", 2)
        self.assertEqual(
            str(context3.exception),
            "Number of children per parent must be a positive integer."
        )

        with self.assertRaises(ValueError) as context4:
            CompositeTree.create_custom_composite_tree_with_params(3, "two")
        self.assertEqual(
            str(context4.exception),
            "Depth of the tree must be a positive integer."
        )


class TestCompositeTreeConfirmInput(unittest.TestCase):

    @patch('builtins.print')
    @patch('Verteilung.composite_tree.CompositeTree.confirm_input',
           return_value=False)
    def test_confirm_input_breaks_loop(
            self, mock_confirm_input, mock_print):
        """
        Tests whether the loop is correctly terminated when the user rejects the input.
        """
        with patch('Verteilung.util.nodes_for_composite.input_positive_number',
                   side_effect=[2, 3]):

            CompositeTree.create_custom_composite_tree()

            mock_confirm_input.assert_any_call(
                "Do you want to create another composite tree? [y/n]: ")
            mock_print.assert_any_call("Exiting the tree creation process.")


class TestCompositeTreeFileMonitoring(unittest.TestCase):

    @patch('Verteilung.composite_tree.Observer')
    def test_start_file_monitoring(self, mock_observer):
        """
        Tests whether the filesystem monitoring is correctly started.
        """
        mock_event_handler = MagicMock()
        mock_observer_instance = mock_observer.return_value

        with patch('Verteilung.composite_tree.CompositeTree.NewJobFileHandler',
                   return_value=mock_event_handler):
            CompositeTree._CompositeTree__start_file_monitoring("/fake/directory")

        mock_observer_instance.schedule.assert_called_once_with(
            mock_event_handler, "/fake/directory", recursive=False)
        mock_observer_instance.start.assert_called_once()

    @patch('Verteilung.composite_tree.Observer')
    def test_stop_file_monitoring(self, mock_observer):
        """
        Tests whether the filesystem monitoring is correctly stopped.
        """
        mock_observer_instance = mock_observer.return_value
        CompositeTree._CompositeTree__observer = mock_observer_instance

        CompositeTree._CompositeTree__stop_file_monitoring()

        mock_observer_instance.stop.assert_called_once()
        mock_observer_instance.join.assert_called_once()
        self.assertIsNone(CompositeTree._CompositeTree__observer)


class TestProcessJobFile(unittest.TestCase):

    @patch('builtins.open',
           new_callable=unittest.mock.mock_open,
           read_data="job_id: 123\nstatus: SUCCESS\nnode_name: ComputeNode1")
    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name',
           return_value=MagicMock(spec=ComputeNode))
    def test_process_job_file_success(self, mock_find_node, mock_open):
        """
        Tests whether the job file is correctly processed when the job was successful.
        """
        mock_compute_node = mock_find_node.return_value

        CompositeTree._process_job_file("/fake/path/job_file.txt")

        mock_find_node.assert_called_once_with("ComputeNode1")
        mock_compute_node.set_running.assert_called_once_with(False)

    @patch('builtins.open',
           new_callable=unittest.mock.mock_open,
           read_data="job_id: 123\nstatus: FAILED\nnode_name: ComputeNode1")
    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name',
           return_value=MagicMock(spec=ComputeNode))
    def test_process_job_file_failure(self, mock_find_node, mock_open):
        """
        Tests whether the job file is correctly processed when the job fails.
        """
        mock_compute_node = mock_find_node.return_value

        CompositeTree._process_job_file("/fake/path/job_file.txt")

        mock_find_node.assert_called_once_with("ComputeNode1")
        mock_compute_node.set_running.assert_not_called()

    @patch('builtins.open',
           new_callable=unittest.mock.mock_open,
           read_data="job_id: 123\nstatus: SUCCESS\nnode_name: InvalidNode")
    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name',
           return_value=None)
    def test_process_job_file_node_not_found(self, mock_find_node, mock_open):
        """
        Tests whether the job file is correctly processed when the node is not found.
        """
        CompositeTree._process_job_file("/fake/path/job_file.txt")

        mock_find_node.assert_called_once_with("InvalidNode")


class TestProcessJobFileExceptionHandling(unittest.TestCase):

    @patch('builtins.open', side_effect=Exception("Test Exception"))
    def test_process_job_file_exception(self, mock_open):
        """
        Tests whether the 'except' block in _process_job_file is reached when an exception occurs.
        """
        with patch('builtins.print') as mock_print:
            CompositeTree._process_job_file("/fake/path/job_file.txt")

            mock_print.assert_any_call(
                "Error processing job file '/fake/path/job_file.txt': Test Exception")


class TestVisualizeTreeExceptionHandling(unittest.TestCase):

    @patch('graphviz.Digraph.render', side_effect=Exception("Test Exception"))
    def test_visualize_tree_exception(self, mock_render):
        """
        Tests whether the 'except' block in visualize_tree is reached when an exception occurs.
        """
        with patch('builtins.print') as mock_print:
            CompositeTree.visualize_tree(output_path="fake_path")

            mock_print.assert_any_call(
                "Error generating tree visualization: Test Exception")


class TestAddNodesToGraph(unittest.TestCase):

    @patch('graphviz.Digraph.node')
    @patch('graphviz.Digraph.edge')
    def test_add_nodes_to_graph(self, mock_edge, mock_node):
        """
        Tests whether the _add_nodes_to_graph method correctly adds nodes and edges.
        """
        root = ManagementNode()
        child1 = ManagementNode(parent=root)
        child2 = ComputeNode()
        root.add(child1)
        root.add(child2)

        dot = Digraph()

        CompositeTree._add_nodes_to_graph(dot, root)

        mock_node.assert_any_call(str(root), label=str(root))
        mock_node.assert_any_call(str(child1), label=str(child1))
        mock_node.assert_any_call(str(child2), label=str(child2))

        mock_edge.assert_any_call(str(root), str(child1))
        mock_edge.assert_any_call(str(root), str(child2))


class TestCompositeTreeInteractiveNodeAddition(unittest.TestCase):

    @patch('builtins.input', side_effect=['ManagementNode', 'root'])
    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__add_node')
    def test_add_management_node_to_root(
            self, mock_add_node, mock_input):
        """
        Tests the interactive addition of a ManagementNode to the root node.
        """
        CompositeTree.add_node_interactively()

        mock_add_node.assert_called_once()
        self.assertTrue(mock_input.called)

    @patch('builtins.input', side_effect=['ComputeNode', 'root'])
    @patch('Verteilung.composite_tree.ComputeNode')
    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__add_node')
    def test_add_compute_node_to_root(
            self, mock_add_node, mock_compute_node, mock_input):
        """
        Tests the interactive addition of a ComputeNode to the root node.
        """
        CompositeTree.add_node_interactively()

        mock_add_node.assert_called_once_with(
            mock_compute_node(), CompositeTree.get_root())

    @patch('builtins.input', side_effect=['InvalidNode', 'root'])
    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__add_node')
    def test_add_invalid_node_type(
            self, mock_add_node, mock_input):
        """
        Tests entering an invalid node type.
        """
        CompositeTree.add_node_interactively()

        mock_add_node.assert_not_called()
        self.assertTrue(mock_input.called)

    @patch('builtins.input', side_effect=['ComputeNode', 'NonExistentParent'])
    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name',
           return_value=None)
    @patch('builtins.print')
    def test_add_node_to_non_existent_parent(
            self, mock_print, mock_find_node, mock_input):
        """
        Tests adding a node to a non-existent parent node.
        """
        CompositeTree.add_node_interactively()

        mock_print.assert_called_once_with(
            "No node with name 'NonExistentParent' found.")


class TestCompositeTreeNodeAdditionErrorHandling(unittest.TestCase):

    @patch('builtins.input', side_effect=['ComputeNode', 'root'])
    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__add_node',
           side_effect=Exception("Test Exception"))
    def test_add_node_exception_handling(
            self, mock_add_node, mock_input):
        """
        Tests whether the 'except' block in add_node_interactively is reached when an exception occurs.
        """
        captured_output = StringIO()
        sys.stdout = captured_output

        CompositeTree.add_node_interactively()

        sys.stdout = sys.__stdout__

        self.assertIn(
            "Error adding node: Test Exception",
            captured_output.getvalue()
        )


class TestCompositeTreeRemoveNode(unittest.TestCase):

    @patch('builtins.input', return_value='TestNode')
    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name')
    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__remove_node')
    @patch('builtins.print')
    def test_remove_node_success(
            self, mock_print, mock_remove_node, mock_find_node, mock_input):
        """
        Tests the successful removal of a node from the CompositeTree.
        """
        mock_node = MagicMock(spec=ManagementNode)
        mock_parent_node = CompositeTree.get_root()
        mock_node.get_parent.return_value = mock_parent_node
        mock_find_node.return_value = mock_node

        CompositeTree.remove_node_interactively()

        mock_remove_node.assert_called_once_with(
            mock_node, mock_parent_node)
        mock_print.assert_called_once_with(
            "Node with name 'TestNode' removed successfully.")

    @patch('builtins.input', return_value='NonExistentNode')
    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name',
           return_value=None)
    @patch('builtins.print')
    def test_remove_node_not_found(
            self, mock_print, mock_find_node, mock_input):
        """
        Tests the scenario when the node to be removed is not found.
        """
        CompositeTree.remove_node_interactively()

        mock_print.assert_called_once_with(
            "No node with name 'NonExistentNode' found.")

    @patch('builtins.input', return_value='RunningNode')
    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name')
    @patch('Verteilung.composite_tree.CompositeTree._has_running_compute_node',
           return_value=True)
    @patch('builtins.print')
    def test_remove_node_running_node(
            self, mock_print, mock_has_running_node, mock_find_node,
            mock_input):
        """
        Tests the scenario when the node or one of its descendants is still running.
        """
        mock_node = MagicMock(spec=ComputeNode)
        mock_find_node.return_value = mock_node

        CompositeTree.remove_node_interactively()

        mock_print.assert_called_once_with(
            "Cannot remove node 'RunningNode' because it or one of its "
            "descendants is currently running.")

    @patch('builtins.input', return_value='TestNode')
    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name')
    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__remove_node',
           side_effect=Exception("Test Exception"))
    @patch('builtins.print')
    def test_remove_node_exception(
            self, mock_print, mock_remove_node, mock_find_node,
            mock_input):
        """
        Tests the 'except' block when an exception occurs while removing the node.
        """
        mock_node = MagicMock(spec=ManagementNode)
        mock_find_node.return_value = mock_node

        CompositeTree.remove_node_interactively()

        mock_print.assert_called_once_with(
            "Error removing node: Test Exception")


class TestCompositeTreeFindNode(unittest.TestCase):

    def setUp(self):
        """Sets up a simple tree structure for the tests."""
        self.root = ManagementNode()
        self.child1 = ManagementNode(parent=self.root)
        self.child2 = ComputeNode()
        self.child3 = ManagementNode(parent=self.child1)

        self.root.add(self.child1)
        self.root.add(self.child2)
        self.child1.add(self.child3)

        CompositeTree._CompositeTree__root = self.root

    def test_find_root_node(self):
        """Tests whether the root node is correctly found."""
        result = CompositeTree._find_node_by_name(str(self.root))
        self.assertEqual(result, self.root, "The root node should be found.")

    def test_find_child_node(self):
        """Tests whether a direct child is correctly found."""
        result = CompositeTree._find_node_by_name(str(self.child1))
        self.assertEqual(result, self.child1,
                         "The child (ManagementNode) should be found.")

    def test_find_grandchild_node(self):
        """Tests whether a deep child (grandchild) is correctly found."""
        result = CompositeTree._find_node_by_name(str(self.child3))
        self.assertEqual(result, self.child3,
                         "The grandchild node should be found.")

    def test_find_nonexistent_node(self):
        """Tests whether None is returned when the node does not exist."""
        result = CompositeTree._find_node_by_name("NonExistentNode")
        self.assertIsNone(result, "None should be returned if the node does not exist.")


class TestCompositeTreeHasRunningComputeNode(unittest.TestCase):

    def setUp(self):
        """Sets up a tree structure with ManagementNodes and ComputeNodes."""
        self.root = ManagementNode()
        self.child1 = ManagementNode(parent=self.root)
        self.child2 = ComputeNode()
        self.child3 = ManagementNode(parent=self.child1)
        self.child4 = ComputeNode()

        self.root.add(self.child1)
        self.root.add(self.child2)
        self.child1.add(self.child3)
        self.child3.add(self.child4)

        CompositeTree._CompositeTree__root = self.root

    def test_no_compute_node_is_running(self):
        """Tests whether False is returned when no ComputeNode is running."""
        self.child2.is_running = MagicMock(return_value=False)
        self.child4.is_running = MagicMock(return_value=False)

        result = CompositeTree._has_running_compute_node(self.root)
        self.assertFalse(result,
                         "False should be returned when no ComputeNode is running.")

    def test_one_compute_node_is_running(self):
        """Tests whether True is returned when one ComputeNode is running."""
        self.child2.is_running = MagicMock(return_value=True)
        self.child4.is_running = MagicMock(return_value=False)

        result = CompositeTree._has_running_compute_node(self.root)
        self.assertTrue(result,
                        "True should be returned when a ComputeNode is running.")

    def test_deep_compute_node_is_running(self):
        """Tests whether True is returned when a deep ComputeNode is running."""
        self.child2.is_running = MagicMock(return_value=False)
        self.child4.is_running = MagicMock(return_value=True)

        result = CompositeTree._has_running_compute_node(self.root)
        self.assertTrue(result,
                        "True should be returned when a deep ComputeNode is running.")

    def test_no_compute_nodes_present(self):
        """Tests whether False is returned when no ComputeNodes are present."""
        self.child1.is_running = MagicMock(return_value=False)
        self.child3.is_running = MagicMock(return_value=False)

        result = CompositeTree._has_running_compute_node(self.root)
        self.assertFalse(result,
                         "False should be returned when no ComputeNodes are present.")


class TestCompositeTreeComputeNodeCounting(unittest.TestCase):

    def setUp(self):
        """Sets up a tree structure with ManagementNodes and ComputeNodes."""
        self.root = ManagementNode()
        self.child1 = ManagementNode(parent=self.root)
        self.child2 = ComputeNode()
        self.child3 = ManagementNode(parent=self.child1)
        self.child4 = ComputeNode()

        self.root.add(self.child1)
        self.root.add(self.child2)
        self.child1.add(self.child3)
        self.child3.add(self.child4)

        CompositeTree._CompositeTree__root = self.root

    def test_count_all_compute_nodes(self):
        """Tests the count_compute_nodes method to count the total number of ComputeNodes."""
        count = CompositeTree.count_compute_nodes(self.root)
        self.assertEqual(count, 2,
                         "There should be 2 ComputeNodes counted.")

    def test_count_no_compute_nodes(self):
        """Tests count_compute_nodes for a node that contains no ComputeNodes."""
        empty_node = ManagementNode()
        count = CompositeTree.count_compute_nodes(empty_node)
        self.assertEqual(count, 0,
                         "There should be no ComputeNodes counted.")

    def test_count_not_running_compute_nodes(self):
        """Tests count_not_running_compute_nodes to count the number of non-running ComputeNodes."""
        self.child2.is_running = MagicMock(return_value=False)
        self.child4.is_running = MagicMock(return_value=False)

        count = CompositeTree.count_not_running_compute_nodes(self.root)
        self.assertEqual(count, 2,
                         "There should be 2 non-running ComputeNodes counted.")

    def test_count_running_compute_nodes(self):
        """Tests count_not_running_compute_nodes when some ComputeNodes are running."""
        self.child2.is_running = MagicMock(return_value=True)
        self.child4.is_running = MagicMock(return_value=False)

        count = CompositeTree.count_not_running_compute_nodes(self.root)
        self.assertEqual(count, 1,
                         "There should be only 1 non-running ComputeNode counted.")


class TestCompositeTreeNodeCallback(unittest.TestCase):

    def setUp(self):
        """Sets up a tree structure with ManagementNodes and ComputeNodes."""
        self.root = ManagementNode()
        self.child1 = ComputeNode()
        self.root.add(self.child1)

        CompositeTree._CompositeTree__root = self.root

    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name',
           return_value=None)
    def test_node_not_found(self, mock_find_node):
        """Tests handle_node_callback when the node is not found."""
        with patch('builtins.print') as mock_print:
            CompositeTree.handle_node_callback('UnknownNode')
            mock_print.assert_called_once_with(
                "No node with name 'UnknownNode' found.")

    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name')
    def test_node_not_a_compute_node(self, mock_find_node):
        """Tests handle_node_callback when the found node is not a ComputeNode."""
        mock_find_node.return_value = ManagementNode()

        with patch('builtins.print') as mock_print:
            CompositeTree.handle_node_callback('NonComputeNode')
            mock_print.assert_called_once_with(
                "Node 'NonComputeNode' is not a ComputeNode.")

    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name')
    def test_successful_node_callback(self, mock_find_node):
        """Tests handle_node_callback when the node is successfully found and the flag is set."""
        mock_compute_node = MagicMock(spec=ComputeNode)
        mock_find_node.return_value = mock_compute_node

        with patch('builtins.print') as mock_print:
            CompositeTree.handle_node_callback('ComputeNode1')
            mock_compute_node.set_running.assert_called_once_with(False)
            mock_print.assert_called_with(
                "Node 'ComputeNode1' running flag set to False.")


class TestCompositeTreeNodeCallbackErrorHandling(unittest.TestCase):

    @patch('Verteilung.composite_tree.CompositeTree._find_node_by_name',
           side_effect=Exception("Test Exception"))
    def test_handle_node_callback_exception(self, mock_find_node):
        """
        Tests the 'except' block when an exception occurs while finding the node.
        """
        with patch('builtins.print') as mock_print:
            CompositeTree.handle_node_callback('ComputeNode1')

            mock_print.assert_called_once_with(
                "Error handling callback for node 'ComputeNode1': Test Exception")


class TestCompositeTreeSimulation(unittest.TestCase):

    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__start_file_monitoring')
    def test_simulation_started_on_correct_nodes(
            self, mock_start_monitoring):
        """
        Tests whether the simulation is started on the correct ComputeNodes and initiates directory monitoring.
        """
        root = ManagementNode()
        compute_node1 = MagicMock(spec=ComputeNode)
        compute_node1.is_running.return_value = False
        compute_node2 = MagicMock(spec=ComputeNode)
        compute_node2.is_running.return_value = False

        root.add(compute_node1)
        root.add(compute_node2)

        CompositeTree._CompositeTree__observer = None

        CompositeTree._run_simulation(
            root,
            num_compute_nodes_to_use=2,
            replications_per_node=5,
            slurm_account='test_account',
            slurm_username='test_user',
            model_script='model_script.py',
            time_limit=60,
            cpus_per_task=2
        )

        mock_start_monitoring.assert_called_once_with(
            path_to_monitor=r"\util\flask\test")

        compute_node1.distribute_and_compute.assert_called_once_with(
            model='model_script.py',
            num_replications=5,
            slurm_account='test_account',
            slurm_username='test_user',
            model_script='model_script.py',
            time_limit=60,
            cpus_per_task=2
        )
        compute_node2.distribute_and_compute.assert_called_once_with(
            model='model_script.py',
            num_replications=5,
            slurm_account='test_account',
            slurm_username='test_user',
            model_script='model_script.py',
            time_limit=60,
            cpus_per_task=2
        )

    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__start_file_monitoring')
    def test_simulation_limits_nodes(
            self, mock_start_monitoring):
        """
        Tests whether the simulation starts on the correct number of ComputeNodes when the limit is reached.
        """
        root = ManagementNode()
        compute_node1 = MagicMock(spec=ComputeNode)
        compute_node1.is_running.return_value = False
        compute_node2 = MagicMock(spec=ComputeNode)
        compute_node2.is_running.return_value = False
        compute_node3 = MagicMock(spec=ComputeNode)
        compute_node3.is_running.return_value = False

        root.add(compute_node1)
        root.add(compute_node2)
        root.add(compute_node3)

        CompositeTree._CompositeTree__observer = None

        CompositeTree._run_simulation(
            root,
            num_compute_nodes_to_use=2,
            replications_per_node=5,
            slurm_account='test_account',
            slurm_username='test_user',
            model_script='model_script.py',
            time_limit=60,
            cpus_per_task=2
        )

        compute_node1.distribute_and_compute.assert_called_once_with(
            model='model_script.py',
            num_replications=5,
            slurm_account='test_account',
            slurm_username='test_user',
            model_script='model_script.py',
            time_limit=60,
            cpus_per_task=2
        )
        compute_node2.distribute_and_compute.assert_called_once_with(
            model='model_script.py',
            num_replications=5,
            slurm_account='test_account',
            slurm_username='test_user',
            model_script='model_script.py',
            time_limit=60,
            cpus_per_task=2
        )
        compute_node3.distribute_and_compute.assert_not_called()

    @patch('Verteilung.composite_tree.CompositeTree._CompositeTree__start_file_monitoring')
    def test_simulation_stops_if_no_available_nodes(
            self, mock_start_monitoring):
        """
        Tests whether the simulation correctly aborts when no ComputeNodes are available.
        """
        root = ManagementNode()
        compute_node1 = MagicMock(spec=ComputeNode)
        compute_node1.is_running.return_value = True

        root.add(compute_node1)

        CompositeTree._CompositeTree__observer = None

        CompositeTree._run_simulation(
            root,
            num_compute_nodes_to_use=1,
            replications_per_node=5,
            slurm_account='test_account',
            slurm_username='test_user',
            model_script='model_script.py',
            time_limit=60,
            cpus_per_task=2
        )

        compute_node1.distribute_and_compute.assert_not_called()
        mock_start_monitoring.assert_called_once_with(
            path_to_monitor=r"\util\flask\test")

    @patch('Verteilung.composite_tree.CompositeTree.count_compute_nodes',
           return_value=10)
    @patch('Verteilung.composite_tree.CompositeTree.count_not_running_compute_nodes',
           return_value=5)
    @patch('Verteilung.composite_tree.CompositeTree._run_simulation')
    def test_adjusting_compute_nodes(
            self, mock_run_simulation, mock_count_not_running,
            mock_count_total):
        """
        Tests whether the number of ComputeNodes is correctly adjusted when more are requested than available.
        """
        with patch('builtins.print') as mock_print:
            CompositeTree.start_simulation(
                num_replications=100,
                num_compute_nodes=10,  # Requested compute nodes
                slurm_account="test_account",
                slurm_username="test_user",
                model_script="model.py",
                time_limit=120,
                cpus_per_task=4
            )

            mock_print.assert_any_call(
                "Adjusting compute nodes to available number: 5")
            mock_run_simulation.assert_called_once()

    @patch('Verteilung.composite_tree.CompositeTree.count_compute_nodes',
           return_value=10)
    @patch('Verteilung.composite_tree.CompositeTree.count_not_running_compute_nodes',
           return_value=0)
    def test_simulation_stops_if_no_available_nodes(
            self, mock_count_not_running, mock_count_total):
        """
        Tests whether the simulation stops when no ComputeNodes are available.
        """
        with patch('builtins.print') as mock_print:
            CompositeTree.start_simulation(
                num_replications=100,
                num_compute_nodes=5,
                slurm_account="test_account",
                slurm_username="test_user",
                model_script="model.py",
                time_limit=120,
                cpus_per_task=4
            )

            mock_print.assert_any_call("No Compute Nodes available for computing")


class TestCompositeTreeConfirmInput(unittest.TestCase):

    @patch('builtins.input', return_value='y')
    def test_confirm_input_yes(self, mock_input):
        """
        Tests the input confirmation for 'y'.
        """
        self.assertTrue(CompositeTree.confirm_input("Are you sure?"))

    @patch('builtins.input', return_value='n')
    def test_confirm_input_no(self, mock_input):
        """
        Tests the input confirmation for 'n'.
        """
        self.assertFalse(CompositeTree.confirm_input("Are you sure?"))


class TestCompositeTreeAdditionalNodes(unittest.TestCase):

    @patch('Verteilung.composite_tree.CompositeTree.add_node_interactively')
    @patch('builtins.print')
    def test_create_additional_compute_nodes(
            self, mock_print, mock_add_node):
        """
        Tests the creation of additional ComputeNodes.
        """
        CompositeTree._create_additional_compute_nodes(3)
        self.assertEqual(mock_add_node.call_count, 3)
        mock_print.assert_called_once_with(
            "Created 3 additional ComputeNodes.")


class TestCompositeTreeSimulationError(unittest.TestCase):

    @patch('Verteilung.composite_tree.CompositeTree.count_compute_nodes',
           side_effect=Exception("Test Exception"))
    @patch('builtins.print')
    def test_start_simulation_exception(
            self, mock_print, mock_count_compute_nodes):
        """
        Tests the 'except' block in start_simulation when an exception occurs.
        """
        CompositeTree.start_simulation(
            10, 5, 'test_account', 'test_user',
            'model_script.py', 60, 2)
        mock_print.assert_called_once_with(
            "Error starting simulation: Test Exception")


class TestCompositeTreeMainFunction(unittest.TestCase):

    @patch('Verteilung.composite_tree.CompositeTree.create_custom_composite_tree')
    def test_singleton_behavior(
            self, mock_create_custom_tree):
        """
        Tests the singleton behavior and the call chain in the main function.
        """
        with patch('builtins.print') as mock_print:
            main()

            self.assertEqual(mock_print.call_count, 2)
            printed_ids = [call[0][0] for call in mock_print.call_args_list]
            self.assertEqual(printed_ids[0], printed_ids[1])

            mock_create_custom_tree.assert_called_once()


if __name__ == '__main__':
    unittest.main()
