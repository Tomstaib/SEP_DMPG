from __future__ import annotations

import os
from time import time

from graphviz import Digraph

from models.model_pcb import setup_model_pcb
from util.nodes_for_composite import ManagementNode, Node, input_positive_number, ComputeNode
from util.singleton import Singleton


class CompositeTree(metaclass=Singleton):
    __root: ManagementNode = ManagementNode()
    __replications_per_node: int = 0

    @classmethod
    def __add_node(cls, node: Node, parent: ManagementNode = None):
        if parent is None:
            parent = cls.__root
        parent.add(node)

    @classmethod
    def __remove_node(cls, node: Node, parent: ManagementNode = None):
        if parent is None:
            parent = cls.__root
        parent.remove(node)

    @classmethod
    def get_root(cls) -> ManagementNode:
        return cls.__root

    @classmethod
    def destroy_composite_tree(cls) -> None:
        cls.__root = ManagementNode()

    @classmethod
    def get_replications_per_node(cls) -> int:
        return cls.__replications_per_node

    @classmethod
    def set_replications_per_node(cls, num_replications: int) -> None:
        cls.__replications_per_node = num_replications

    @classmethod
    def create_custom_composite_tree(cls):
        """
        Create a custom composite tree with user input. A tree is symmetric since another form wouldn't make more sense
        """
        try:
            while True:
                num_replications: int = input_positive_number(
                    "Please enter number of replications you wish to simulate")
                num_children_per_parent: int = input_positive_number(
                    "Please enter how many children a Management Node should have")
                depth_of_tree: int = input_positive_number("Please enter the depth of the tree")

                num_compute_nodes = num_children_per_parent ** (depth_of_tree - 1)
                replications_per_node = num_replications / num_compute_nodes
                cls.set_replications_per_node(int(round(replications_per_node)))

                print(f"Each ComputeNode will handle approximately {round(replications_per_node)} replications.")
                confirm = input("Do you want to proceed with these settings? [y/n]: ").strip().lower()

                if confirm == 'y':
                    cls.destroy_composite_tree()

                    current_level_nodes: list = [cls.__root]

                    for depth in range(depth_of_tree):
                        next_level_nodes: list = []
                        for parent_node in current_level_nodes:
                            for child_index in range(num_children_per_parent):
                                if depth == depth_of_tree - 1:
                                    child_node: ComputeNode = ComputeNode()
                                else:
                                    child_node: ManagementNode = ManagementNode(parent=parent_node)
                                parent_node.add(child_node)
                                next_level_nodes.append(child_node)
                        current_level_nodes = next_level_nodes

                    break
                else:
                    retry = input("Do you want to create another composite tree? [y/n]: ").strip().lower()
                    if retry != 'y':
                        print("Exiting the tree creation process.")
                        break

        except Exception as e:
            print(f"Error: {str(e)}")

    @classmethod
    def visualize_tree(cls):
        """simply visualize the tree to verify the correct structure"""
        try:
            dot = Digraph(comment='CompositeTree')
            cls._add_nodes_to_graph(dot, cls.__root)
            dot_path = 'CompositeTree.gv'
            dot.render(dot_path, view=True)  # This will create and open the .gv file
            print(f"Graphviz file created at: {os.path.abspath(dot_path)}")
        except Exception as e:
            print(f"Error generating graphviz file: {str(e)}")

    @staticmethod
    def _add_nodes_to_graph(dot: Digraph, node: Node):
        dot.node(node.__str__(), label=node.__str__())
        if isinstance(node, ManagementNode):
            for child in node:
                dot.edge(node.__str__(), child.__str__())
                CompositeTree._add_nodes_to_graph(dot, child)

    @classmethod
    def add_node_interactively(cls):
        """Interactively adds a node to the tree."""
        try:
            node_type = input("Enter the type of node to add (ManagementNode/ComputeNode): ").strip()
            parent_name = input("Enter the name of the parent node (or 'root' to add to the root): ").strip()

            if parent_name.lower() == 'root':
                parent_node = cls.__root
            else:
                parent_node = cls._find_node_by_name(parent_name)
                if parent_node is None:
                    print(f"No node with name '{parent_name}' found.")
                    return

            if node_type == 'ManagementNode':
                new_node = ManagementNode(parent=parent_node)
            elif node_type == 'ComputeNode':
                new_node = ComputeNode()
            else:
                print("Invalid node type.")
                return

            cls.__add_node(new_node, parent_node)
            print(f"Node added successfully under parent '{parent_name}'.")
        except Exception as e:
            print(f"Error adding node: {str(e)}")

    @classmethod
    def remove_node_interactively(cls):
        """Interactively removes a node from the tree."""
        try:
            node_name = input("Enter the name of the node to remove: ").strip()
            node_to_remove = cls._find_node_by_name(node_name)

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
    def _find_node_by_name(cls, name: str, current_node: Node = None) -> Node | None:
        """Helper method to find a node by its name."""
        if current_node is None:
            current_node = cls.__root

        if current_node.__str__() == name:
            return current_node

        if isinstance(current_node, ManagementNode):
            for child in current_node:
                result = cls._find_node_by_name(name, child)
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
        """Counts the number of ComputeNodes under the given ManagementNode."""
        count = 0

        def _count_compute_nodes_recursively(node: ManagementNode):
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
        """Counts the number of ComputeNodes that are not running under the given ManagementNode."""
        count = 0

        def _count_not_running_compute_nodes_recursively(node: ManagementNode):
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
            # Find the node by name
            compute_node = cls._find_node_by_name(node_name)

            # Ensure the node exists and is a ComputeNode
            if compute_node is None:
                print(f"No node with name '{node_name}' found.")
                return

            if not isinstance(compute_node, ComputeNode):
                print(f"Node '{node_name}' is not a ComputeNode.")
                return

            # Set the running flag to False
            compute_node.set_running(False)
            print(f"Node '{node_name}' running flag set to False.")

        except Exception as e:
            print(f"Error handling callback for node '{node_name}': {str(e)}")


def main():
    start: float = time()
    composite_tree1: CompositeTree = CompositeTree()
    print(id(composite_tree1))
    composite_tree2: CompositeTree = CompositeTree()
    print(id(composite_tree2))
    print(composite_tree1 is composite_tree2)
    composite_tree2.create_custom_composite_tree()
    composite_tree2.visualize_tree()
    composite_tree2.add_node_interactively()
    composite_tree2.visualize_tree()
    composite_tree2.remove_node_interactively()
    composite_tree2.visualize_tree()
    # root: ManagementNode = create_composite_tree(NUM_REPLICATIONS)
    # root: ManagementNode = create_custom_composite_tree()
    composite_tree2.get_root().distribute_and_compute(setup_model_pcb, 15, composite_tree2.get_replications_per_node())
    finish: float = time()
    print("Time taken", finish - start)


if __name__ == '__main__':
    main()
