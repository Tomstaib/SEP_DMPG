from enum import Enum


class QueueType(Enum):
    """
    Enumeration defining the order in which elements are processed in a queue.

    Attributes:
        FIFO: First-In-First-Out order. Elements are processed in the order they were added.
        LIFO: Last-In-First-Out order. The last element added is processed first.
    """
    FIFO = 0
    LIFO = 1
