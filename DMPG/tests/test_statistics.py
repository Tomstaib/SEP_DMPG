import unittest
from src.core.server import Server
from src.core.entity import Entity
from src.core.sink import Sink
from src.util.simulations import calculate_units_utilized, create_pivot
import simpy


class TestStatistics(unittest.TestCase):
    def setUp(self):
        self.env = simpy.Environment()

    def test_units_utilized_calculation(self):
        # This test case checks if the units utilized calculation works correctly.
        server = Server(self.env, "TestServerStats", capacity=2,
                        processing_time_distribution_with_parameters=(lambda: 2,))
        sink = Sink(self.env, "TestSink")
        server.connect(sink)

        entities = [Entity(f"Entity{i + 1}", self.env.now) for i in range(4)]
        for entity in entities:
            server.handle_entity_arrival(entity)

        self.env.run(until=4)

        expected_units_utilized = 2
        actual_units_utilized = calculate_units_utilized(server.units_utilized_over_time, server.capacity, self.env.now)
        self.assertAlmostEqual(expected_units_utilized, actual_units_utilized,
                               msg="Calculated units utilized does not match the expected result")

    def test_average_processing_time(self):
        # This test checks the average processing time calculation for entities in a server.
        server = Server(self.env, "TestServerAvgProcTime", capacity=1,
                        processing_time_distribution_with_parameters=(lambda: 3,))
        sink = Sink(self.env, "TestSink")
        server.connect(sink)

        for _ in range(5):
            server.handle_entity_arrival(Entity("TestEntity", self.env.now))
        self.env.run(until=100)

        expected_avg_processing_time = 3  # Assuming fixed processing time of 3
        actual_avg_processing_time = server.total_processing_time_pivot_table / server.entities_processed
        self.assertEqual(expected_avg_processing_time, actual_avg_processing_time,
                         "Average processing time is not as expected")

    def test_system_throughput(self):
        # This test case checks the system throughput calculation.
        server = Server(self.env, "TestServerThroughput", capacity=2,
                        processing_time_distribution_with_parameters=(lambda: 4,))
        sink = Sink(self.env, "TestSinkThroughput")
        server.connect(sink)

        self.env.run(until=100)

        expected_throughput = server.entities_processed / self.env.now
        actual_throughput = len(sink.processed_entities) / self.env.now
        self.assertAlmostEqual(expected_throughput, actual_throughput,
                               msg="System throughput calculation is incorrect")

    def test_create_pivot_table(self):
        # Test the pivot table creation from simulation statistics
        entity_stats = {'NumberCreated': 10, 'NumberDestroyed': 8}
        server_stats = [{'Server': 'Server1', 'ScheduledUtilization': 80, 'UnitsUtilized': 1.2}]
        combiner_stats = [{}]
        separator_stats = [{}]
        sink_stats = {'Sink1': {'AvgTimeInSystem': 5.0}}
        source_stats = {'Source1': {'NumberExited': 8}}

        pivot_table = create_pivot([entity_stats], {'Server1': server_stats},
                                   {'Combiner1': [combiner_stats]},
                                   {'Separator1': [separator_stats]},
                                   {'Sink1': [sink_stats['Sink1']]},
                                   {'Source1': [source_stats['Source1']]},
                                   ['NumberCreated', 'NumberDestroyed'],
                                   ['ScheduledUtilization', 'UnitsUtilized'],
                                   [], [],
                                   ['AvgTimeInSystem'], ['NumberExited'])

        # Check if the pivot table includes correct stats for each component
        self.assertIn(('Entity', 'Entity', 'NumberCreated'), pivot_table.index,
                      "Pivot table missing Entity NumberCreated statistic")
        self.assertIn(('Server', 'Server1', 'ScheduledUtilization'), pivot_table.index,
                      "Pivot table missing Server ScheduledUtilization statistic")
        self.assertIn(('Sink', 'Sink1', 'AvgTimeInSystem'), pivot_table.index,
                      "Pivot table missing Sink AvgTimeInSystem statistic")
        self.assertIn(('Source', 'Source1', 'NumberExited'), pivot_table.index,
                      "Pivot table missing Source NumberExited statistic")


if __name__ == '__main__':
    unittest.main()
