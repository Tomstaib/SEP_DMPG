from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from models.model_pcb import setup_model_pcb
from src.util.simulations import run_replications, run_simulation
from time import time

MINIMUM_OF_REPLICATIONS_FOR_COMPOSITE: int = 1000  # just an example
NUM_REPLICATIONS: int = 1000000  # example normally would get this from the website


class Node(ABC):
    """
    Abstract base class for all Node Objects
    """

    @abstractmethod
    def operation(self, model, minutes: int, num_replications: int) -> None:
        pass


class ManagementNode(Node):
    """
    Node for distributing workload to compute Nodes
    """
    instance_count: int = 0

    def __init__(self, parent: Optional['ManagementNode'] = None):
        self.__class__.instance_count += 1
        self._name: str = f'ManagementNode{self.__class__.instance_count}'
        self._parent: ManagementNode | None = parent
        self.__children: list[Node] = []

    def operation(self, model, minutes: int, num_replications: int) -> None:
        for child in self.__children:
            child.operation(model, minutes, num_replications)
        if self._parent:
            self._parent.notify(f"{self._name} completed its operations.", self)

    def get_number_of_children(self) -> int:
        return len(self.__children)

    def add(self, component: Node) -> None:
        self.__children.append(component)

    def remove(self, component: Node) -> None:
        self.__children.remove(component)

    def notify(self, message: str, node: 'ManagementNode') -> None:
        """
        Exemplary implementation for a notification if the Slurm job is completed
        :param message: e.g. "Completed the Slurm job"
        :param node: sender of the notification
        :return:
        """
        print(f"{node._name} notifies {self._name}: {message}")

    def count_compute_nodes(self) -> int:
        count: int = 0
        for child in self.__children:
            if isinstance(child, ComputeNode):
                count += 1
            elif isinstance(child, ManagementNode):
                count += child.count_compute_nodes()
        return count

    def __str__(self) -> str:
        return self._name


class ComputeNode(Node):
    """
    Node for computing
    """
    instance_count: int = 0

    def __init__(self, callback=None):
        self.__class__.instance_count += 1
        self._name: str = f'ComputeNode{self.__class__.instance_count}'
        self.callback = callback

    def operation(self, model, minutes, num_replications):
        """
        examplary implementation for a computation. Normally here the slurm job would be submitted
        """
        run_simulation(model=model, minutes=minutes)
        run_replications(model=model, minutes=minutes, num_replications=num_replications, multiprocessing=True)
        if self.callback:
            self.callback("Completed simulation", self)


def create_composite_tree(num_replications: int) -> ManagementNode:
    """
    Create a composite tree of Management and Compute Nodes based on a given number of replications
    :param num_replications: Number of replications needed
    :return: The root of the tree with a whole tree below itself
    """

    root: ManagementNode = ManagementNode()

    if num_replications < MINIMUM_OF_REPLICATIONS_FOR_COMPOSITE:
        root.add(ComputeNode())
        return root

    depth: int = compute_tree_sizes(num_replications)
    add_nodes(root, 1, depth)
    return root


def add_nodes(parent: ManagementNode, current_depth: int, max_depth: int):
    if current_depth < max_depth:
        for _ in range(2):
            child: ManagementNode = ManagementNode(parent=parent)
            parent.add(child)
            add_nodes(child, current_depth + 1, max_depth)
    else:
        for _ in range(2):
            compute_node: ComputeNode = ComputeNode(callback=parent.notify)
            parent.add(compute_node)


def compute_tree_sizes(num_replications: int) -> int:
    total_number_of_management_nodes = (num_replications // 1000)  # 1000 is exemplary there would need to be a
    # more spohisticated solution in the final implementation

    management_nodes_per_level: int = 1
    counter: int = 1

    while management_nodes_per_level * 2 <= total_number_of_management_nodes:
        management_nodes_per_level *= 2
        counter += 1

    return counter


def main():
    start: float = time()
    root: ManagementNode = create_composite_tree(NUM_REPLICATIONS)
    replications_per_node = NUM_REPLICATIONS / root.count_compute_nodes()
    print("compute nodes", root.count_compute_nodes())
    print("num children", root.get_number_of_children())
    replications_per_node = round(replications_per_node)
    print("replications per node", replications_per_node)
    root.operation(setup_model_pcb, 15, replications_per_node)
    finish: float = time()
    print("Time taken", finish - start)


if __name__ == '__main__':
    main()
