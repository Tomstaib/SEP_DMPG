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
    def add_node(cls, node: Node):
        cls.__root.add(node)

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

                # this computation is wrong ?if the tree size is 2?
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
        """simply visualize the tree to verify the correct strcture"""
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
        dot.node(str(id(node)), label=node.__str__())
        # ManagementNode could also be Node but warning in next line because node could be not iterable
        if isinstance(node, ManagementNode):
            for child in node:
                dot.edge(str(id(node)), str(id(child)))
                CompositeTree._add_nodes_to_graph(dot, child)


def main():
    start: float = time()
    composite_tree1: CompositeTree = CompositeTree()
    print(composite_tree1)
    composite_tree2: CompositeTree = CompositeTree()
    print(composite_tree2)
    print(composite_tree1 is composite_tree2)
    composite_tree2.create_custom_composite_tree()
    composite_tree2.visualize_tree()
    # root: ManagementNode = create_composite_tree(NUM_REPLICATIONS)
    # root: ManagementNode = create_custom_composite_tree()
    composite_tree2.get_root().distribute_and_compute(setup_model_pcb, 15, composite_tree2.get_replications_per_node())
    finish: float = time()
    print("Time taken", finish - start)


if __name__ == '__main__':
    main()
