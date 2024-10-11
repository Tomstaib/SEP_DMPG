import sys
import os
import time
from typing import Optional
from graphviz import Digraph

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Verteilung')))
from Verteilung.util.flask.nodes_for_composite import ManagementNode, Node, input_positive_number, ComputeNode
from Verteilung.util.singleton import Singleton
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class CompositeTree(metaclass=Singleton):
    """
    The CompositeTree class is used to distribute simulations to multiple jobs. It consists of a root that is always a
    ManagementNode in our case (and many other Management Nodes) but also Compute Nodes. The metaclass is Singleton as
    there always only should be one CompositeTree for one user.

    See also:
        -[ManagementNode](../util/flask/nodes_for_composite.html#ManagementNode)
        -[ComputeNode](../util/flask/nodes_for_composite.html#ComputeNode)
        -[Singleton](../util/singleton.html#Singleton)
    """
    __root: ManagementNode = ManagementNode()
    """The root node for all computation"""

    __replications_per_node: int = 0
    """The number of replication compute node"""

    __observer: Optional[FileSystemEventHandler] = None
    """The observer for job file handling"""

    @classmethod
    def __add_node(cls, node: Node, parent: ManagementNode = None):
        """Adds a Node to a parent that must be a ManagementNode"""
        if parent is None:
            parent = cls.__root
        parent.add(node)

    @classmethod
    def __remove_node(cls, node: Node, parent: ManagementNode = None):
        """Removes a Node from a parent that must be a ManagementNode"""
        if parent is None:
            parent = cls.__root
        parent.remove(node)

    @classmethod
    def get_root(cls) -> ManagementNode:
        return cls.__root

    @classmethod
    def destroy_composite_tree(cls) -> None:
        """"Reset/Destroy" the CompositeTree"""
        cls.__root = ManagementNode()

    @classmethod
    def get_replications_per_node(cls) -> int:
        """Get the replications per ComputeNode"""
        return cls.__replications_per_node

    @classmethod
    def set_replications_per_node(cls, num_replications: int) -> None:
        """Set the replications per ComputeNode"""
        if num_replications < 0:
            raise ValueError("Number of replications per node must be non-negative.")
        cls.__replications_per_node = num_replications

    @classmethod
    def create_custom_composite_tree(cls):
        """
        Create a custom composite tree with user input. A tree is symmetric since another form wouldn't make more sense.
        """
        try:
            while True:

                num_children_per_parent: int = input_positive_number(
                    "Please enter how many children a Management Node should have")
                depth_of_tree: int = input_positive_number("Please enter the depth of the tree")

                if cls.confirm_input(f"Do you want to proceed with these settings? [y/n]:"
                                     f"\nDepth of the tree: {depth_of_tree}"
                                     f"\nNumber of children per parent: {num_children_per_parent}"
                                     f"\nTotal number of compute Nodes: {num_children_per_parent ** depth_of_tree}"):
                    cls.destroy_composite_tree()

                    current_level_nodes: list[ManagementNode] = [cls.__root]

                    cls.__build_composite_tree(current_level_nodes, depth_of_tree, num_children_per_parent)

                    break
                else:
                    if not cls.confirm_input("Do you want to create another composite tree? [y/n]: "):
                        print("Exiting the tree creation process.")
                        break

        except Exception as e:
            print(f"Error: {str(e)}")

    @classmethod
    def __build_composite_tree(cls, current_level_nodes: list[Optional[ManagementNode]],
                               depth_of_tree: int, num_children_per_parent: int):
        """Build the composite tree based on provided inputs."""
        for depth in range(depth_of_tree):
            next_level_nodes: list = []
            for parent_node in current_level_nodes:
                for _ in range(num_children_per_parent):
                    if depth == depth_of_tree - 1:
                        child_node: ComputeNode = ComputeNode()
                    else:
                        child_node: ManagementNode = ManagementNode(parent=parent_node)
                    parent_node.add(child_node)
                    next_level_nodes.append(child_node)
            current_level_nodes = next_level_nodes

    @classmethod
    def create_custom_composite_tree_with_params(cls, num_children_per_parent: int,
                                                depth_of_tree: int) -> Optional[ManagementNode]:
        """
        Create a custom composite tree with the provided number of children per parent and tree depth.
        Returns the root of the created tree.
        """
        # Eingabevalidierung
        if not isinstance(num_children_per_parent, int) or num_children_per_parent <= 0:
            raise ValueError("Number of children per parent must be a positive integer.")
        if not isinstance(depth_of_tree, int) or depth_of_tree <= 0:
            raise ValueError("Depth of the tree must be a positive integer.")
        
        try:
            # Vorherigen Baum löschen
            cls.destroy_composite_tree()

            current_level_nodes: list[ManagementNode] = [cls.__root]

            cls.__build_composite_tree(current_level_nodes, depth_of_tree, num_children_per_parent)

            print(
                f"Composite tree with depth {depth_of_tree} and {num_children_per_parent} children per parent created.")

            return cls.__root

        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    @classmethod
    def __start_file_monitoring(cls, path_to_monitor: str) -> None:
        """
        Start file monitoring. With a daemon

        :param path_to_monitor: Path to the directory to monitor.

        See also:
            -[NewJobFileHandler](../util/flask/composite_tree.html#NewJobFileHandler)
        """
        event_handler = cls.NewJobFileHandler()
        cls.__observer = Observer()
        cls.__observer.schedule(event_handler, path_to_monitor, recursive=False)
        cls.__observer.start()
        print(f"Started monitoring directory: {path_to_monitor}")

    @classmethod
    def __stop_file_monitoring(cls):
        """Stop the file monitoring observer."""
        if cls.__observer:
            cls.__observer.stop()
            cls.__observer.join()
            cls.__observer = None
            print("Stopped monitoring directory.")

    @classmethod
    def _process_job_file(cls, file_path: str) -> None:
        """Process the job file and update the ComputeNode status."""
        try:
            with open(file_path, 'r') as file:
                job_info = file.read().splitlines()

            job_id = job_info[0].split(': ')[1]
            status = job_info[1].split(': ')[1]
            node_name = job_info[2].split(': ')[1]

            print(f"Processing job file for node: {node_name} with status: {status}")

            # Find the ComputeNode by name
            compute_node = cls._find_node_by_name(node_name)

            if compute_node and isinstance(compute_node, ComputeNode):
                if status == "SUCCESS":
                    compute_node.set_running(False)
                    print(f"Node '{node_name}' running flag set to False.")
                else:
                    print(f"Job '{job_id}' for node '{node_name}' did not succeed.")
            else:
                print(f"ComputeNode '{node_name}' not found.")

        except Exception as e:
            print(f"Error processing job file '{file_path}': {str(e)}")

    class NewJobFileHandler(FileSystemEventHandler, metaclass=Singleton):
        """Handles events when a new job file is created. Works with a daemon to prevent polling."""

        def on_created(self, event):
            if not event.is_directory:
                composite_tree_cls = CompositeTree
                file_path = event.src_path
                print(f"New file detected: {file_path}")

                time.sleep(1)  # Delay to ensure file is ready for reading

                composite_tree_cls._process_job_file(file_path)

    @classmethod
    def visualize_tree(cls, output_path: str = 'src/util/flask'):
        """Visualize the tree and save it as a PNG file in the specified output path."""
        try:
            dot: Digraph = Digraph(comment='CompositeTree')
            cls._add_nodes_to_graph(dot, cls.__root)

            # Save as png
            dot.render(output_path, format='png', cleanup=True)

        except Exception as e:
            print(f"Error generating tree visualization: {str(e)}")

    @staticmethod
    def _add_nodes_to_graph(dot: Digraph, node: Node):
        """Adds nodes to Graphviz graph"""
        dot.node(node.__str__(), label=node.__str__())
        if isinstance(node, ManagementNode):
            for child in node:
                dot.edge(node.__str__(), child.__str__())
                CompositeTree._add_nodes_to_graph(dot, child)

    @classmethod
    def add_node_interactively(cls):
        """Interactively adds a node to the tree based on its name."""
        try:
            node_type: str = input("Enter the type of node to add (ManagementNode/ComputeNode): ").strip()
            parent_name: str = input("Enter the name of the parent node (or 'root' to add to the root): ").strip()

            if parent_name.lower() == 'root':
                parent_node: ManagementNode = cls.__root
            else:
                parent_node: Optional[ManagementNode] = cls._find_node_by_name(parent_name)
                if parent_node is None:
                    print(f"No node with name '{parent_name}' found.")
                    return

            if node_type == 'ManagementNode':
                new_node: ManagementNode = ManagementNode(parent=parent_node)
            elif node_type == 'ComputeNode':
                new_node: ComputeNode = ComputeNode()
            else:
                print("Invalid node type.")
                return

            cls.__add_node(new_node, parent_node)
            print(f"Node added successfully under parent '{parent_name}'.")
        except Exception as e:
            print(f"Error adding node: {str(e)}")

    @classmethod
    def remove_node_interactively(cls):
        """Interactively removes a node from the tree based on its name."""
        try:
            node_name: str = input("Enter the name of the node to remove: ").strip()
            node_to_remove: Optional[Node] = cls._find_node_by_name(node_name)

            if node_to_remove is None:
                print(f"No node with name '{node_name}' found.")
                return

            if cls._has_running_compute_node(node_to_remove):
                print(f"Cannot remove node '{node_name}' because it or one of its descendants is currently running.")
                return

            parent_node = node_to_remove.get_parent() if node_to_remove.get_parent() is not None else cls.__root
            cls.__remove_node(node_to_remove, parent_node)
            print(f"Node with name '{node_name}' removed successfully.")
        except Exception as e:
            print(f"Error removing node: {str(e)}")

    @classmethod
    def _find_node_by_name(cls, name: str, current_node: Node = None) -> Optional[Node]:
        """Helper method to find a node by its name."""
        if current_node is None:
            current_node: ManagementNode = cls.__root

        if current_node.__str__() == name:
            return current_node

        if isinstance(current_node, ManagementNode):
            for child in current_node:
                result: Optional[Node] = cls._find_node_by_name(name, child)
                if result is not None:
                    return result

        return None

    @classmethod
    def _has_running_compute_node(cls, node: Node) -> bool:
        """Helper method to check if a node or its children have running ComputeNodes."""
        if isinstance(node, ComputeNode) and node.is_running():
            return True

        if isinstance(node, ManagementNode):
            for child in node:
                if cls._has_running_compute_node(child):
                    return True

        return False

    @classmethod
    def count_compute_nodes(cls, management_node: ManagementNode) -> int:
        """
        Counts the number of ComputeNodes under the given ManagementNode. There is a local function to do it
        recursively.
        """
        count = 0

        def _count_compute_nodes_recursively(node: ManagementNode):
            """Recursively counts the number of ComputeNodes under the given ManagementNode."""
            nonlocal count
            for child in node:
                if isinstance(child, ComputeNode):
                    count += 1
                elif isinstance(child, ManagementNode):
                    _count_compute_nodes_recursively(child)

        _count_compute_nodes_recursively(management_node)
        return count

    @classmethod
    def count_not_running_compute_nodes(cls, management_node: ManagementNode) -> int:
        """
        Counts the number of ComputeNodes that are not running under the given ManagementNode. There is a local
        function to do it recursively.
        """
        count: int = 0

        def _count_not_running_compute_nodes_recursively(node: ManagementNode):
            """Recursively counts the number of ComputeNodes that are not running under the given ManagementNode."""
            nonlocal count
            for child in node:
                if isinstance(child, ComputeNode) and not child.is_running():
                    count += 1
                elif isinstance(child, ManagementNode):
                    _count_not_running_compute_nodes_recursively(child)

        _count_not_running_compute_nodes_recursively(management_node)
        return count

    @classmethod
    def handle_node_callback(cls, node_name: str) -> None:
        """
        Callback handler that sets the 'running' flag of the given ComputeNode to False.

        :param node_name: The name of the ComputeNode that finished its task.
        """
        try:
            compute_node = cls._find_node_by_name(node_name)

            # Ensure the node exists and is a ComputeNode
            if compute_node is None:
                print(f"No node with name '{node_name}' found.")
                return

            if not isinstance(compute_node, ComputeNode):
                print(f"Node '{node_name}' is not a ComputeNode.")
                return

            compute_node.set_running(False)
            print(f"Node '{node_name}' running flag set to False.")

        except Exception as e:
            print(f"Error handling callback for node '{node_name}': {str(e)}")

    @staticmethod
    def confirm_input(prompt: str = "Please confirm your input") -> bool:
        """User is prompted to confirm input by pressing "y"."""
        confirm: str = input(prompt).strip().lower()

        if confirm == "y":
            return True
        else:
            return False

    @classmethod
    def start_simulation(cls, num_replications: int, num_compute_nodes: int, slurm_account: str,
                         slurm_username: str, model_script: str, time_limit: int, cpus_per_task: int):
        """
        Starts the simulation from the root node.

        :param num_replications: The total number of replication to simulate.
        :param num_compute_nodes: The number of compute nodes to simulate on.
        :param slurm_account: The Slurm account to be billed.
        :param slurm_username: The Slurm username to be used.
        :param model_script: The model script to be used.
        :param time_limit: The time limit for the Slurm job in minutes.
        :param cpus_per_task: Number of CPUs per task for the simulation.
        """
        try:
            total_compute_nodes: int = cls.count_compute_nodes(cls.__root)
            not_running_compute_nodes: int = cls.count_not_running_compute_nodes(cls.__root)

            print(f"Total ComputeNodes: {total_compute_nodes}")
            print(f"ComputeNodes available for simulation (not running): {not_running_compute_nodes}")

            if num_compute_nodes > not_running_compute_nodes:
                num_compute_nodes: int = not_running_compute_nodes
                print(f"Adjusting compute nodes to available number: {num_compute_nodes}")

            if num_compute_nodes == 0:
                print("No Compute Nodes available for computing")
                return

            replications_per_node: int = round(num_replications / num_compute_nodes)

            print(f"Simulation will be started with {num_compute_nodes} Compute Nodes "
                  f"and {replications_per_node} replications per node")

            cls._run_simulation(cls.__root, num_compute_nodes, replications_per_node, slurm_account, slurm_username,
                                model_script, time_limit, cpus_per_task)

        except Exception as e:
            print(f"Error starting simulation: {str(e)}")

    @classmethod
    def _create_additional_compute_nodes(cls, num_nodes: int):
        """
        Creates additional ComputeNodes to satisfy the simulation requirements.
        """
        created_nodes: int = 0

        while created_nodes < num_nodes:
            cls.add_node_interactively()
            created_nodes += 1

        print(f"Created {num_nodes} additional ComputeNodes.")

    @classmethod
    def _run_simulation(cls, management_node: ManagementNode, num_compute_nodes_to_use: int, replications_per_node: int,
                        slurm_account: str, slurm_username: str, model_script: str, time_limit: int,
                        cpus_per_task: int) -> None:
        """
        Recursive method to start the simulation on the specified number of ComputeNodes with the given parameters.
        """
        count: int = 0

        # Start monitoring the directory for job completion files
        if cls.__observer is None:
            cls.__start_file_monitoring(path_to_monitor=r"\util\flask\test")

        def _simulate_on_node(node: Node):
            nonlocal count
            if count >= num_compute_nodes_to_use:
                return

            if isinstance(node, ComputeNode) and not node.is_running():
                node.distribute_and_compute(model=model_script, num_replications=replications_per_node,
                                            slurm_account=slurm_account, model_script=model_script,
                                            time_limit=time_limit, slurm_username=slurm_username,
                                            cpus_per_task=cpus_per_task)
                count += 1

            if isinstance(node, ManagementNode):
                for child in node:
                    _simulate_on_node(child)

        _simulate_on_node(management_node)
        print(f"Simulation started on {count} ComputeNodes.")


def main():
    composite_tree1: CompositeTree = CompositeTree()
    print(id(composite_tree1))
    composite_tree2: CompositeTree = CompositeTree()
    print(id(composite_tree2))
    assert id(composite_tree1) == id(composite_tree2)
    composite_tree2.create_custom_composite_tree()


if __name__ == '__main__':
    main() #pragma: no cover