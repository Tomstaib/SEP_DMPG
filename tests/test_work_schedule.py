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
    DateTime.set(datetime(2024, 12, 12, 0, 0, 0))

    workday = WorkScheduleDay()
    workday.set_time(9, 0, 13, 0)
    workday.set_time(14, 0, 16, 0)
    workday.set_time(18, 0, 19, 0)

    friday = WorkScheduleDay()
    friday.set_time(8, 30, 13, 0)

    weekend = WorkScheduleDay()

    week = WorkScheduleWeek(
        workday, workday, workday, workday, friday, weekend, weekend
    )
    source1 = Source(env, "Source1", (random.expovariate, 1 / 1.25))
    server1 = Server(env, "Server1", (random.expovariate, 1), week)
    sink1 = Sink(env, "Sink1")

    source1.connect(server1)
    server1.connect(sink1)


class TestCases(unittest.TestCase):

    def test_single_run(self):
        pivot_table = run_simulation(model=setup_working_schedule, minutes=1440)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Value'], 560.7848)  # 567.109 ? see test_model4_1.py

    def test_sequential_replications(self):
        pivot_table = run_replications(model=setup_working_schedule, minutes=1440, num_replications=10,
                                       multiprocessing=False)

        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'], 506.6157)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'], 534.0338)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'], 567.1098)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Half-Width'], 11.4856)

    def test_parallel_replications(self):
        pivot_table = run_replications(model=setup_working_schedule, minutes=1440, num_replications=10,
                                       multiprocessing=True)

        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'], 506.6157)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'], 534.0338)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'], 567.1098)
        self.assertEqual(pivot_table.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Half-Width'], 11.4856)
