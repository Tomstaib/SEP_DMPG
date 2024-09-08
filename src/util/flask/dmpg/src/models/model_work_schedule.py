from src.util.global_imports import random
from src.core.source import Source
from src.core.server import Server
from src.core.sink import Sink
from src.util.simulations import run_simulation
from src.util.work_schedule import (WorkScheduleDay, WorkScheduleWeek)
from src.util.date_time import DateTime
from datetime import datetime


def setup_work_schedule(env):
    DateTime.set(datetime(2024, 4, 1, 2, 0, 0))

    workday = WorkScheduleDay()
    workday.set_time(0, 0, 6, 0)
    workday.set_time(6, 0, 12, 0)
    workday.set_time(12, 0, 18, 0)
    workday.set_time(18, 0, 24, 0)

    friday = WorkScheduleDay()
    friday.set_time(8, 30, 13, 30)

    weekend = WorkScheduleDay()

    week = WorkScheduleWeek(
        workday, workday, workday, workday, friday, weekend, weekend
    )
    week.print_stats("week")

    source1 = Source(env, "Source1", (random.expovariate, 1 / 1.25))
    server1 = Server(env, "Server1", (random.expovariate, 1), week)
    sink1 = Sink(env, "Sink1")

    source1.connect(server1)
    server1.connect(sink1)


def main():
    run_simulation(model=setup_work_schedule, minutes=1440)  # 1 day

    """
    run_replications(model=setup_work_schedule, minutes=1440, num_replications=10, multiprocessing=False)
    run_replications(model=setup_work_schedule, minutes=1440, num_replications=10, multiprocessing=True)
    print(pivot_table3.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Minimum'])
    print(pivot_table3.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Average'])
    print(pivot_table3.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Maximum'])
    print(pivot_table3.at[('Entity', 'Entity', 'AvgTimeInSystem'), 'Half-Width'])
    """


if __name__ == '__main__':
    main()
