import unittest
from src.util.singleton import Singleton


class SingletonTester(metaclass=Singleton):
    def __init__(self, value):
        self.value = value


class TestSingleton(unittest.TestCase):
    def setUp(self):
        SingletonTester._instance = None  # Reset the Singleton instance for each test

    def test_singleton_instance_creation(self):
        """Test that a Singleton instance is created."""
        obj1 = SingletonTester(10)
        self.assertIsNotNone(obj1)
        self.assertEqual(obj1.value, 10)

    def test_singleton_same_instance(self):
        """Test that subsequent calls return the same instance."""
        obj1 = SingletonTester(10)
        obj2 = SingletonTester(20)
        self.assertIs(obj1, obj2)
        self.assertEqual(obj1.value, 10)

    def test_singleton_shared_state(self):
        """Test that state is shared across all instances."""
        obj1 = SingletonTester(10)
        obj2 = SingletonTester(20)
        self.assertEqual(obj1.value, 10)  # Value remains 10 for both obj1 and obj2
        self.assertEqual(obj2.value, 10)

    def test_singleton_reset(self):
        """Test that resetting the instance works as expected."""
        obj1 = SingletonTester(10)
        SingletonTester._instance = None
        obj2 = SingletonTester(30)
        self.assertIsNot(obj1, obj2)  # obj1 and obj2 should now be different instances
        self.assertEqual(obj2.value, 30)  # obj2 should have the new value
