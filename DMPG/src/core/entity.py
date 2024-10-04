from typing import Union
from src.util.singleton import Singleton


class Entity:
    """Represents a generic entity with a name, creation time, and optional destruction time."""
    def __init__(self, name: str, creation_time: Union[int, float], is_parent: bool = True) -> None:
        """
        Initializes an Entity instance with Name, creation_time and destruction_time set to none and adds it to the
        EntityManager class for tracking.

        :param name (str): The name of the entity.
        :param creation_time (Union[int, float]): The creation time of the entity.
        """
        self.name = name
        self.creation_time = creation_time
        self.destruction_time = None
        self.is_parent = is_parent
        self.batch_members = []
        EntityManager.add_entity(self)

    def __repr__(self) -> str:
        """
        Provides a string representation of the Entity instance, showing its lifecycle.

        :return: str: A string representation of the entity, including its name, creation time,
        and destruction time (if any).
        """
        return f"{self.name} ({self.creation_time})" if not self.destruction_time \
            else f"{self.name} ({self.destruction_time - self.creation_time})"


class EntityManager(Singleton):
    """
    Manages a collection of Entity instances. Utilizes the Singleton design pattern to ensure that only one instance of
    this class exists throughout the application.
    This class is responsible for adding entities to a tracking list and for the destruction of all entities
    within that list.
    """
    entities = []
    """List of all existing entities instances"""

    @classmethod
    def add_entity(cls, entity: Entity) -> None:
        """
        Adds an Entity instance to the EntityManager's list for tracking. This method ensures that all entities
        are accounted for and can be managed collectively.

        :param entity: The Entity instance to be added to the tracking list.
        """
        cls.entities.append(entity)

    @classmethod
    def destroy_all_entities(cls) -> None:
        """Destroys all entities managed by the EntityManager by resetting their destruction time
        and clearing them from the tracking list."""
        cls.entities.clear()


class SubEntity(Entity):
    def __init__(self, name: str, creation_time: Union[int, float]) -> None:
        super().__init__(name, creation_time)
        self.num_times_processed = 0
        self.server_history = []
        self.combiner_history = []
        self.separator_history = []
        # EntityManager.add_entity(self)

    def count_processing(self) -> None:
        self.num_times_processed += 1

    def add_to_server_history(self, server: str) -> None:
        self.server_history.append(server)

    def add_to_combiner_history(self, combiner: str) -> None:
        self.combiner_history.append(combiner)

    def add_to_separator_history(self, separator: str) -> None:
        self.separator_history.append(separator)

    def __repr__(self):
        return f"{self.name} ({self.creation_time})" if not self.destruction_time \
            else f"{self.name} ({self.destruction_time - self.creation_time})"
