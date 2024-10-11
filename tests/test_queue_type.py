import unittest
from src.core.queue_type import QueueType

class TestQueueType(unittest.TestCase):
    def test_enum_values(self):
        # Test the value of FIFO
        self.assertEqual(QueueType.FIFO.value, 0)
        # Test the value of LIFO
        self.assertEqual(QueueType.LIFO.value, 1)

    def test_enum_members(self):
        """Test the enum members for proper names"""
        self.assertEqual(QueueType.FIFO.name, 'FIFO')
        self.assertEqual(QueueType.LIFO.name, 'LIFO')

    def test_enum_type(self):
        """Test that the enum members are of the correct type"""
        self.assertIsInstance(QueueType.FIFO, QueueType)
        self.assertIsInstance(QueueType.LIFO, QueueType)

    def test_enum_comparison(self):
        """Test comparison of enum values"""
        self.assertEqual(QueueType.FIFO, QueueType(0))
        self.assertEqual(QueueType.LIFO, QueueType(1))

if __name__ == '__main__':
    unittest.main()
