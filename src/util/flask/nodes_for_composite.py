from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from src.util.flask.job import submit_slurm_job

MINIMUM_OF_REPLICATIONS_FOR_COMPOSITE: int = 1000
"""Exemplary and not necessary but nice to have"""


class Node(ABC):
    """
    Abstract base class for all Node Objects.
    """

    _instance_count: int = 0

    # needed for the getter and setter of parent: throwing failures for unimplemented attributes
    @abstractmethod
    def __init__(self, parent: Optional[ManagementNode] = None):
        self.__class__._instance_count += 1
        self._parent: Optional[ManagementNode] = parent
        """Protected because of name mangling when inheriting"""

        self._name: str = ""
        """Protected because of name mangling when inheriting"""

    def __str__(self) -> str:
        """Return a string representation of the Node."""
        return self._name

    @abstractmethod
    def distribute_and_compute(self, model, num_replications: int,
                               slurm_account: str = None, model_script: str = None, time_limit: int = None,
                               slurm_username: str = None, jwt_token: str = None) -> None:
        """
        Distribute or compute. The Node will interpret the command correctly by type.

        :param model: Model to simulate.
        :param num_replications: Number of replications.
        :param slurm_account: Slurm account name.
        :param model_script: Model script.
        :param time_limit: Time limit for the Slurm job.
        :param slurm_username: Slurm username.
        :param jwt_token: JWT token needed for job submission via REST-API.

        See also:
            - [ManagementNode](../util/flask/nodes_for_composite.html#ManagementNode): Node to manage workload.
            - [ComputeNode](../util/flask/nodes_for_composite.html#ComputeNode): Node to compute the simulation.
        """
        pass

    def get_parent(self) -> Optional[ManagementNode]:
        """Returns the parent of the Node."""
        return self._parent

    def set_parent(self, parent: ManagementNode) -> bool:
        """Sets the parent of the Node."""
        if not isinstance(parent, ManagementNode):
            raise TypeError(f"Expected ManagementNode, got {type(parent)}")
        if self._parent is None:
            self._parent: ManagementNode = parent
            return True
        else:
            raise Warning("This node is already parented")


class ManagementNode(Node):
    """
    Node for distributing workload to compute Nodes.

    See also:
        - [Node](../util/flask/nodes_for_composite.html#Node): Abstract base class for all Node Objects.
    """
    _instance_count: int = 0

    def __init__(self, parent: Optional['ManagementNode'] = None):
        self.__class__._instance_count += 1
        self._name: str = f'ManagementNode{self.__class__._instance_count}'
        self._parent: ManagementNode | None = parent
        self.__children: list[Node] = []

    def __iter__(self):
        return iter(self.__children)

    def distribute_and_compute(self, model, num_replications: int,
                               slurm_account: str = None, model_script: str = None, time_limit: int = None,
                               slurm_username: str = None, jwt_token: str = None) -> None:
        """
        Distribute workload to compute Nodes by recursively calling this method on the children.

        :param model: Model to simulate.
        :param num_replications: Number of replications.
        :param slurm_account: Slurm account name.
        :param model_script: Model script.
        :param time_limit: Time limit for the Slurm job.
        :param slurm_username: Slurm username.
        :param jwt_token: JWT token needed for job submission via REST-API.

        See also:
            - [Node](../util/flask/nodes_for_composite.html#Node): Abstract base class for a Node.
            - [ComputeNode](../util/flask/nodes_for_composite.html#ComputeNode): Node to compute the simulation.
        """
        for child in self:
            child.distribute_and_compute(model=model, num_replications=num_replications,
                                         slurm_account=slurm_account, model_script=model_script,
                                         time_limit=time_limit, slurm_username=slurm_username, jwt_token=jwt_token)

        if self._parent:
            self._parent.notify(f"{self.__str__()} completed its operations.", self)

    def get_number_of_children(self) -> int:
        """Returns the number of children of the Node."""
        return len(self.__children)

    def add(self, component: Node) -> None:
        """Add a Node to the list of children."""
        self.__children.append(component)

    def remove(self, component: Node) -> None:
        """Remove a Node from the list of children."""
        self.__children.remove(component)

    def notify(self, message: str, node: 'ManagementNode') -> None:
        """
        Exemplary implementation for a notification if the Slurm job is completed.

        :param message: e.g. "Completed the Slurm job"
        :param node: sender of the notification

        """
        print(f"{node.__str__()} notifies {self.__str__()}: {message}")

    def count_compute_nodes(self) -> int:
        """Count the number of compute nodes and return it."""
        count: int = 0
        for child in self.__children:
            if isinstance(child, ComputeNode):
                count += 1
            elif isinstance(child, ManagementNode):
                count += child.count_compute_nodes()
        return count


class ComputeNode(Node):
    """
    Node for computing/submitting a slurm job.

    See also:
        - [Node](../util/flask/nodes_for_composite.html#Node): Abstract base class for all Node Objects.
    """
    _instance_count: int = 0
    _running: bool = False

    def __init__(self, callback=None):
        self.__class__._instance_count += 1
        self._name: str = f'ComputeNode{self.__class__._instance_count}'
        self.callback = callback

    def is_running(self) -> bool:
        """Checks if the compute node is running and returns a bool."""
        return self._running

    def set_running(self, state: bool) -> None:
        """Set the running flag for the compute node."""
        self._running = state

    def distribute_and_compute(self, model, num_replications: int,
                               slurm_account: str = None, model_script: str = None, time_limit: int = None,
                               slurm_username: str = None, jwt_token: str = None) -> None:
        """
        Submit a slurm job to simulate.

        :param model: Model to simulate.
        :param num_replications: Number of replications.
        :param slurm_account: Slurm account name.
        :param model_script: Model script.
        :param time_limit: Time limit for the Slurm job.
        :param slurm_username: Slurm username.
        :param jwt_token: JWT token needed for job submission via REST-API.

        See also:
            - [Node](../util/flask/nodes_for_composite.html#Node): Abstract base class for a Node.
            - [ManagementNode](../util/flask/nodes_for_composite.html#ManagementNode): Node to distribute the simulation.
        """
        self.set_running(True)
        submit_slurm_job(
            slurm_username=slurm_username,
            slurm_account=slurm_account,
            slurm_jwt=jwt_token,
            job_name=self.__str__(),
            base_url='https://slurm.hpc.hs-osnabrueck.de/slurm/v0.0.39',
            model_script=model_script,
            replications=num_replications,
            time_limit_minutes=time_limit
        )

        if self.callback:
            self.callback("Simulation abgeschlossen", self)
            self.set_running(False)


def input_positive_number(prompt: str = "Please enter a positive number") -> int:
    """Helper function to input a positive number."""
    try:
        positive_number: int = int(input(prompt))

        if positive_number <= 0:
            raise ValueError("Entered number must be greater than zero")
        return positive_number
    except ValueError as e:
        print(f"Error: {e}!")
        return input_positive_number(prompt=prompt)


def create_composite_tree(num_replications: int) -> ManagementNode:
    """
    !!!Depreciated!!!
    Create a composite tree of Management and Compute Nodes based on a given number of replications.
    :param num_replications: Number of replications needed
    :return: The root of the tree with a whole tree below itself
    """

    root: ManagementNode = ManagementNode()

    if num_replications < MINIMUM_OF_REPLICATIONS_FOR_COMPOSITE:
        root.add(ComputeNode())
        return root

    depth: int = compute_tree_sizes(num_replications)
    add_nodes_for_default(root, 1, depth)
    return root


def add_nodes_for_default(parent: ManagementNode, current_depth: int, max_depth: int):
    """
    !!!Depreciated!!!
    Adds nodes for the default tree.
    """
    if current_depth < max_depth:
        for _ in range(2):
            child: ManagementNode = ManagementNode(parent=parent)
            parent.add(child)
            add_nodes_for_default(child, current_depth + 1, max_depth)
    else:
        for _ in range(2):
            compute_node: ComputeNode = ComputeNode(callback=parent.notify)
            parent.add(compute_node)


def compute_tree_sizes(num_replications: int) -> int:
    """
    !!!Depreciated!!!
    Computes the tree size of a default tree.
    """
    total_number_of_management_nodes = (num_replications // 1000)  # 1000 is exemplary

    management_nodes_per_level: int = 1
    counter: int = 1

    while management_nodes_per_level * 2 <= total_number_of_management_nodes:
        management_nodes_per_level *= 2
        counter += 1

    return counter
