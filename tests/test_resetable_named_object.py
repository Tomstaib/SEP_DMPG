import unittest
import simpy

from src.core.resetable_named_object import ResetAbleNamedObjectManager, ResetAbleNamedObject


class ConcreteResetAbleNamedObject(ResetAbleNamedObject):
    def reset(self):
        self.reset_called = True

    def __repr__(self):
        return f"ConcreteResetAbleNamedObject({self.name})"


class TestResetAbleNamedObjectManager(unittest.TestCase):

    def setUp(self):
        self.env = simpy.Environment()
        self.manager = ResetAbleNamedObjectManager()

    def test_add_method(self):
        # Test if objects are added correctly
        obj1 = ConcreteResetAbleNamedObject(self.env, 'obj1', self.manager)
        obj2 = ConcreteResetAbleNamedObject(self.env, 'obj2', self.manager)
        self.assertEqual(len(self.manager.resetable_named_objects), 2)
        self.assertIn(obj1, self.manager.resetable_named_objects)
        self.assertIn(obj2, self.manager.resetable_named_objects)

    def test_iteration(self):
        # Test the iterator and __next__ methods
        obj1 = ConcreteResetAbleNamedObject(self.env, 'obj1', self.manager)
        obj2 = ConcreteResetAbleNamedObject(self.env, 'obj2', self.manager)

        # Convert manager to an iterator and test
        iterator = iter(self.manager)
        self.assertEqual(next(iterator), obj1)
        self.assertEqual(next(iterator), obj2)
        with self.assertRaises(StopIteration):
            next(iterator)

    def test_reset_all(self):
        # Test if reset_all calls reset on all objects
        obj1 = ConcreteResetAbleNamedObject(self.env, 'obj1', self.manager)
        obj2 = ConcreteResetAbleNamedObject(self.env, 'obj2', self.manager)

        obj1.reset_called = False
        obj2.reset_called = False

        self.manager.reset_all()

        self.assertTrue(obj1.reset_called)
        self.assertTrue(obj2.reset_called)

    def test_repr(self):
        # Test the __repr__ method
        obj1 = ConcreteResetAbleNamedObject(self.env, 'obj1', self.manager)
        obj2 = ConcreteResetAbleNamedObject(self.env, 'obj2', self.manager)

        expected_repr = "ResetAbleNamedObjects(2 objects: ConcreteResetAbleNamedObject(obj1), ConcreteResetAbleNamedObject(obj2))"
        self.assertEqual(repr(self.manager), expected_repr)


class TestResetAbleNamedObject(unittest.TestCase):

    def setUp(self):
        self.env = simpy.Environment()
        self.manager = ResetAbleNamedObjectManager()

    def test_abstract_class_instantiation(self):
        # You cannot instantiate an abstract class directly
        with self.assertRaises(TypeError):
            ResetAbleNamedObject(self.env, 'test_obj', self.manager)

    def test_concrete_reset_method(self):
        # Test that the concrete class properly implements reset
        obj = ConcreteResetAbleNamedObject(self.env, 'obj1', self.manager)
        obj.reset_called = False
        obj.reset()
        self.assertTrue(obj.reset_called)

    def test_concrete_repr(self):
        # Test the __repr__ implementation for concrete class
        obj = ConcreteResetAbleNamedObject(self.env, 'obj1', self.manager)
        self.assertEqual(repr(obj), "ConcreteResetAbleNamedObject(obj1)")


if __name__ == '__main__':
    unittest.main()
