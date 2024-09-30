from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Type

from util.simulations import run_replications, run_simulation

MINIMUM_OF_REPLICATIONS_FOR_COMPOSITE: int = 10  # just an example
NUM_REPLICATIONS: int = 10000  # example normally would get this from the website


class Node(ABC):
    """
    Abstract base class for all Node Objects
    """

    _instance_count: int = 0

    # needed for the getter and setter of parent: throwing failures for unimplemented attributes
    @abstractmethod
    def __init__(self, parent: Optional[ManagementNode] = None):
        self.__class__._instance_count += 1
        self._parent: ManagementNode | None = parent
        self._name: str = ""

    def __str__(self) -> str:
        return self._name

    @abstractmethod
    def distribute_and_compute(self, model, minutes: int, num_replications: int) -> None:
        pass #pragma: no cover

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return False
        return (self._parent == other._parent) and (self._name == other._name)  

    def __repr__(self) -> str:
        if self._parent is not None:
            parent_repr = f"{self._parent._name} (id={id(self._parent)})"
        else:
            parent_repr = None
        return f"{self.__class__.__name__}(name={self._name}, parent={parent_repr})"

    def get_parent(self) -> ManagementNode | None:
        return self._parent

    def set_parent(self, parent: ManagementNode) -> bool:
        if not isinstance(parent, ManagementNode):
            raise TypeError(f"Expected ManagementNode, got {type(parent)}")
        if self._parent is None:
            self._parent = parent
            return True
        else:
            raise Warning(f"This node is already parented")

class ManagementNode(Node):
    """
    Node for distributing workload to compute Nodes
    """
    _instance_count: int = 0

    def __init__(self, parent: Optional['ManagementNode'] = None):
        self.__class__._instance_count += 1
        self._name: str = f'ManagementNode{self.__class__._instance_count}'
        self._parent: ManagementNode | None = parent
        self.__children: list[Node] = []

    def __iter__(self):
        return iter(self.__children)

    def distribute_and_compute(self, model, minutes: int, num_replications: int) -> None:
        for child in self:
            child.distribute_and_compute(model=model, minutes=minutes, num_replications=num_replications)
        if self._parent:
            self._parent.notify(f"{self.__str__()} completed its operations.", self)

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
        print(f"{node.__str__()} notifies {self.__str__()}: {message}")

    def count_compute_nodes(self) -> int:
        count: int = 0
        for child in self.__children:
            if isinstance(child, ComputeNode):
                count += 1
            elif isinstance(child, ManagementNode):
                count += child.count_compute_nodes()
        return count 
    # Added (Marcel)
    # Needing to add, because in testing the counter for the nodes were getting higher and higher
    @classmethod
    def reset_instance_count(cls):
        cls._instance_count = 0

class ComputeNode(Node):
    """
    Node for computing/submitting a slurm job
    """
    _instance_count: int = 0
    _running: bool = False

    def __init__(self, callback=None):
        self.__class__._instance_count += 1
        self._name: str = f'ComputeNode{self.__class__._instance_count}'
        self.callback = callback

    def is_running(self):
        return self._running

    def set_running(self, state: bool) -> None:
        self._running = state

    def distribute_and_compute(self, model, minutes, num_replications):
        """
        examplary implementation for a computation. Normally here the slurm job would be submitted
        """
        self.set_running(True)
        run_simulation(model=model, minutes=minutes)
        run_replications(model=model, minutes=minutes, num_replications=num_replications, multiprocessing=True)
        if self.callback:
            self.callback("Completed simulation", self)
            self.set_running(False)

    # Added (Marcel)
    # Needing to add, because in testing the counter for the nodes were getting higher and higher
    @classmethod
    def reset_instance_count(cls):
        cls._instance_count = 0

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

# Überarbeitet (Marcel)
def compute_tree_sizes(num_replications: int) -> int:
    if num_replications < 1000: # Aussume, that less than 1000 no tree ist needed
        return 0

    total_number_of_management_nodes = (num_replications // 1000)
    management_nodes_per_level = 1
    counter = 0

    while management_nodes_per_level <= total_number_of_management_nodes:
        management_nodes_per_level *= 2
        counter += 1

    return counter - 1  # Subtract 1 to get the correct number of levels


def input_positive_number(prompt: str = "Please enter a positive number") -> int:

    try:
        positive_number: int = int(input(prompt))

        if positive_number <= 0:
            raise ValueError("Entered number must be greater than zero")
        return positive_number
    except ValueError as e:
        print(f"Error: {e}!")
        return input_positive_number(prompt=prompt)
