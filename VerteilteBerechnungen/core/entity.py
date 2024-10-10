import sys 
import os

from typing import Union

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../VerteilteBerechnungen')))
from VerteilteBerechnungen.util.singleton import Singleton



class Entity:
    def __init__(self, name: str, creation_time: Union[int, float]) -> None:
        self.name = name
        self.creation_time = creation_time
        self.destruction_time = None
        EntityManager.add_entity(self)

    def __repr__(self):
        return f"{self.name} ({self.creation_time})" if not self.destruction_time \
            else f"{self.name} ({self.destruction_time - self.creation_time})"

class EntityManager(Singleton):
    entities = []

    @classmethod
    def add_entity(cls, entity: Entity):
        cls.entities.append(entity)

    @classmethod
    def destroy_all_entities(cls):
        EntityManager.entities.clear()
