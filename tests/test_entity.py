import unittest
from src.core.entity import Entity, EntityManager, SubEntity


class TestEntity(unittest.TestCase):
    def setUp(self):
        # Clear EntityManager before each test
        EntityManager.destroy_all_entities()

    def test_entity_initialization(self):
        entity = Entity(name="TestEntity", creation_time=10)
        self.assertEqual(entity.name, "TestEntity")
        self.assertEqual(entity.creation_time, 10)
        self.assertIsNone(entity.destruction_time)
        self.assertIn(entity, EntityManager.entities)

    def test_entity_repr_without_destruction_time(self):
        entity = Entity(name="TestEntity", creation_time=10)
        expected_repr = "TestEntity (10)"
        self.assertEqual(repr(entity), expected_repr)

    def test_entity_repr_with_destruction_time(self):
        entity = Entity(name="TestEntity", creation_time=10)
        entity.destruction_time = 15
        expected_repr = "TestEntity (5)"
        self.assertEqual(repr(entity), expected_repr)


class TestEntityManager(unittest.TestCase):
    def setUp(self):
        # Clear EntityManager before each test
        EntityManager.destroy_all_entities()

    def test_add_entity(self):
        entity1 = Entity(name="Entity1", creation_time=5)
        entity2 = Entity(name="Entity2", creation_time=10)
        self.assertIn(entity1, EntityManager.entities)
        self.assertIn(entity2, EntityManager.entities)
        self.assertEqual(len(EntityManager.entities), 2)

    def test_destroy_all_entities(self):
        entity1 = Entity(name="Entity1", creation_time=5)
        entity2 = Entity(name="Entity2", creation_time=10)
        EntityManager.destroy_all_entities()
        self.assertEqual(len(EntityManager.entities), 0)


class TestSubEntity(unittest.TestCase):
    def setUp(self):
        # Clear EntityManager before each test
        EntityManager.destroy_all_entities()

    def test_subentity_initialization(self):
        sub_entity = SubEntity(name="TestSubEntity", creation_time=20)
        self.assertEqual(sub_entity.name, "TestSubEntity")
        self.assertEqual(sub_entity.creation_time, 20)
        self.assertIsNone(sub_entity.destruction_time)
        self.assertEqual(sub_entity.num_times_processed, 0)
        self.assertEqual(sub_entity.server_history, [])
        self.assertIn(sub_entity, EntityManager.entities)

    def test_count_processing(self):
        sub_entity = SubEntity(name="TestSubEntity", creation_time=20)
        sub_entity.count_processing()
        self.assertEqual(sub_entity.num_times_processed, 1)
        sub_entity.count_processing()
        self.assertEqual(sub_entity.num_times_processed, 2)

    def test_add_to_server_history(self):
        sub_entity = SubEntity(name="TestSubEntity", creation_time=20)
        sub_entity.add_to_server_history("Server1")
        self.assertEqual(sub_entity.server_history, ["Server1"])
        sub_entity.add_to_server_history("Server2")
        self.assertEqual(sub_entity.server_history, ["Server1", "Server2"])

    def test_subentity_repr_without_destruction_time(self):
        sub_entity = SubEntity(name="TestSubEntity", creation_time=20)
        expected_repr = "TestSubEntity (20)"
        self.assertEqual(repr(sub_entity), expected_repr)

    def test_subentity_repr_with_destruction_time(self):
        sub_entity = SubEntity(name="TestSubEntity", creation_time=20)
        sub_entity.destruction_time = 30
        expected_repr = "TestSubEntity (10)"
        self.assertEqual(repr(sub_entity), expected_repr)


if __name__ == '__main__':
    unittest.main()
