from src.util.singleton import Singleton
from src.core.resetable_named_object import ResetAbleNamedObjectManager
from enum import Enum


class ComponentType(Enum):
    SOURCES = 'Sources'
    SERVERS = 'Servers'
    SINKS = 'Sinks'


class Model(metaclass=Singleton):
    def __init__(self):
        self.components = {
            ComponentType.SOURCES: ResetAbleNamedObjectManager(),
            ComponentType.SERVERS: ResetAbleNamedObjectManager(),
            ComponentType.SINKS: ResetAbleNamedObjectManager()
        }

    def add_component(self, component, component_type):
        self.components[component_type].add(component)

    def get_components(self):
        return {ctype.value: manager for ctype, manager in self.components.items()}
