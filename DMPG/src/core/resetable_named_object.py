import simpy
from abc import ABC, abstractmethod


class ResetAbleNamedObjectManager:

    def __init__(self):
        self.resetable_named_objects = []

    def add(self, rno):
        self.resetable_named_objects.append(rno)

    def __iter__(self):
        self.iteration_object = -1
        return self

    def __next__(self):
        self.iteration_object += 1
        if self.iteration_object < len(self.resetable_named_objects):
            return self.resetable_named_objects[self.iteration_object]
        raise StopIteration

    def reset_all(self):
        for rno in self.resetable_named_objects:
            rno.reset()

        self.resetable_named_objects = []

    def __repr__(self):
        object_details = ", ".join(repr(obj) for obj in self.resetable_named_objects)
        return f'ResetAbleNamedObjects({len(self.resetable_named_objects)} objects: {object_details})'


class ResetAbleNamedObject(ABC):

    def __init__(self, env: simpy.Environment, name: str, rnom: ResetAbleNamedObjectManager):
        self.name = name
        self.env = env
        rnom.add(self)

    @abstractmethod
    def reset(self):
        pass
