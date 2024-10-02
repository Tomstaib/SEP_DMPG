from __future__ import annotations
import time
import os
from abc import ABC, abstractmethod
from typing import Optional, Type

from job import submit_slurm_job
from environment import execute_command

from ssh_setup import setup_ssh_connection

MINIMUM_OF_REPLICATIONS_FOR_COMPOSITE: int = 1000



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
    def distribute_and_compute(self, model, minutes: int, num_replications: int,
                               slurm_account: str = None, model_script: str = None, time_limit: int = None,
                               slurm_username: str = None, jwt_token: str = None) -> None:
        pass

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

    def distribute_and_compute(self, model, minutes: int, num_replications: int,
                               slurm_account: str = None, model_script: str = None, time_limit: int = None,
                               slurm_username: str = None, jwt_token: str = None) -> None:
        """
        Verteilungslogik für die Replikation auf den Management- und Compute-Nodes.
        Rekursiv aufrufen, um den Prozess weiter auf die Compute-Nodes zu verteilen.
        """
        for child in self:
            # Rufe rekursiv distribute_and_compute auf den Kindern auf (kann entweder ManagementNode oder ComputeNode sein)
            child.distribute_and_compute(model=model, minutes=minutes, num_replications=num_replications,
                                         slurm_account=slurm_account, model_script=model_script,
                                         time_limit=time_limit, slurm_username=slurm_username, jwt_token=jwt_token)

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

    def distribute_and_compute(self, model, minutes: int, num_replications: int,
                               slurm_account: str = None, model_script: str = None, time_limit: int = None,
                               slurm_username: str = None, jwt_token: str = None) -> None:
        """
        Beispielhafte Implementierung, bei der der Slurm-Job eingereicht wird.
        """
        self.set_running(True)
        # Übergebe die Parameter an die Job-Submissions-Funktion
        submit_slurm_job(
            slurm_username=slurm_username,  # Benutzername aus der Session
            slurm_account=slurm_account,  # Der ausgewählte Slurm-Account
            slurm_jwt=jwt_token,  # Übergib den JWT-Token als Parameter
            job_name=self.__str__(),
            base_url='https://slurm.hpc.hs-osnabrueck.de/slurm/v0.0.39',
            model_script=model_script,  # Übergebenes Modell
            replications=num_replications,
            time_limit_minutes=time_limit  # Übergebenes Time-Limit
        )

        # Beispielhafte Verzögerung
        if self.callback:
            self.callback("Simulation abgeschlossen", self)
            self.set_running(False)


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
    total_number_of_management_nodes = (num_replications // 1000)  # 1000 is exemplary; there would need to be a
    # more sophisticated solution in the final implementation

    management_nodes_per_level: int = 1
    counter: int = 1

    while management_nodes_per_level * 2 <= total_number_of_management_nodes:
        management_nodes_per_level *= 2
        counter += 1

    return counter


def input_positive_number(prompt: str = "Please enter a positive number") -> int:

    try:
        positive_number: int = int(input(prompt))

        if positive_number <= 0:
            raise ValueError("Entered number must be greater than zero")
        return positive_number
    except ValueError as e:
        print(f"Error: {e}!")
        return input_positive_number(prompt=prompt)

