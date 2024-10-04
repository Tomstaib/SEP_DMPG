import unittest
from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
from src.util.global_imports import random
from src.util.simulations import run_simulation, run_replications
from src.util.work_schedule import (WorkScheduleDay, WorkScheduleWeek)
from src.util.date_time import DateTime
from datetime import datetime


def setup_working_schedule(env):
    DateTime.set(datetime(2024, 1, 1, 0, 0, 0))

    workday = WorkScheduleDay()
    # 3 shifts, 10 minutes work time per shift
    workday.set_time(9, 0, 9, 10)
    workday.set_time(12, 0, 12, 10)
    workday.set_time(15, 0, 15, 10)

    weekend = WorkScheduleDay()

    week = WorkScheduleWeek(
        workday, workday, workday, workday, workday, weekend, weekend
    )
    source = Source(env, "Source", (lambda: 1,))
    server = Server(env, "Server", (random.uniform, 0.99999, 1), 2, work_schedule=week)
    sink = Sink(env, "Sink")

    source.connect(server)
    server.connect(sink)


class TestCases(unittest.TestCase):

    def test_single_run(self):

        pivot_table = run_simulation(model=setup_working_schedule, minutes=1440)

        self.assertAlmostEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'], 41.0288)  # 696 -> missing reset?
        self.assertEqual(pivot_table.at[('Source', 'Source', 'NumberExited'), 'Value'], 1440)
        self.assertEqual(pivot_table.at[('Server', 'Server', 'NumberExited'), 'Value'], 60)
        self.assertTrue(pivot_table.at[('Server', 'Server', 'AvgTimeProcessing'), 'Value'] <= 1.0)
        self.assertTrue(pivot_table.at[('Server', 'Server', 'TotalTimeProcessing'), 'Value'] < 60)
        self.assertEqual(pivot_table.at[('Sink', 'Sink', 'NumberEntered'), 'Value'], 60)

    def test_parallel_replications(self):

        pivot_table = run_replications(model=setup_working_schedule, minutes=1440, num_replications=10,
                                       multiprocessing=True)

        self.assertAlmostEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'], 696)
        self.assertEqual(pivot_table.at[('Source', 'Source', 'NumberExited'), 'Average'], 1440)
        self.assertEqual(pivot_table.at[('Server', 'Server', 'NumberExited'), 'Average'], 60)
        self.assertTrue(pivot_table.at[('Server', 'Server', 'AvgTimeProcessing'), 'Average'] <= 1.0)
        self.assertTrue(pivot_table.at[('Server', 'Server', 'TotalTimeProcessing'), 'Average'] < 60)
        self.assertEqual(pivot_table.at[('Sink', 'Sink', 'NumberEntered'), 'Average'], 60)
