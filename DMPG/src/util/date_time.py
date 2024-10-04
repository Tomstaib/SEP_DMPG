import locale
from datetime import datetime
from datetime import timedelta
from enum import Enum
from typing import Union
from src.util.singleton import Singleton
from src.util.helper import round_value, ROUND_DECIMAL_PLACES
from src.util.global_imports import HOURS_PER_DAY, MINUTES_PER_HOUR, SECONDS_PER_MINUTE


class TimeComponent(Enum):
    """
    An Enum representing basic units of time.
    """
    second = 1
    """A second, represented by the value `1`, as the fundamental unit of time."""
    minute = 60
    """A minute, converted to seconds (`60`), for representing time intervals in minutes."""
    hour = 3600,
    """An hour, converted to seconds (`3600`), allows for specifying time intervals in hours."""

    day = 86400
    """A day, converted to seconds (`86400`), allows for specifying time intervals in days."""

    week = 604800
    """A week, converted to seconds (`604800`), allows for specifying time intervals in weeks."""


class DateTime(Singleton):
    """
    A singleton class representing a date and time.
    """
    initial_date_time = datetime.now()
    """The set date and time when the object is created."""
    simpy_time_mapped_to = TimeComponent.minute
    """The mapped time in minutes."""
    @classmethod
    def set(cls, initial_date_time: datetime) -> None:
        cls.initial_date_time = initial_date_time

    @classmethod
    def get(cls, time_now: Union[float, int] = 0, time_string_from_initial_date: bool = True, get_weekday_hour_minute=False) -> str:
        """

        :param time_now:
        :param from_initial_date:
        :return: Returns a delta between `time_now` and `from_initial_date` if from_initial_date is set
        """

        """match cls.simpy_time_mapped_to:
            case TimeComponent.second:
                delta = timedelta(seconds=time_now)
            case TimeComponent.minute:
                delta = timedelta(minutes=time_now)
            case TimeComponent.hour:
                delta = timedelta(hours=time_now)
            case _:
                delta = timedelta(0)"""

        if cls.simpy_time_mapped_to == TimeComponent.second:
            delta = timedelta(seconds=time_now)
        elif cls.simpy_time_mapped_to == TimeComponent.minute:
            delta = timedelta(minutes=time_now)
        elif cls.simpy_time_mapped_to == TimeComponent.hour:
            delta = timedelta(hours=time_now)
        else:
            delta = timedelta(0)

        if time_string_from_initial_date:
            return "".join([f"{round_value(time_now):<{ROUND_DECIMAL_PLACES}}, ", str(delta), ", ",
                            (cls.initial_date_time + delta).strftime('%a %d %b %Y, %H:%M:%S:%f')])
        if get_weekday_hour_minute:
            initial_date_time = cls.initial_date_time + delta
            return int(initial_date_time.strftime('%u')), int(initial_date_time.strftime('%H')), int(initial_date_time.strftime('%M'))
        else:
            return str(delta)

    @classmethod
    def map(cls, time_component: TimeComponent) -> None:
        """
        Maps the simpy time component to either seconds, minutes or hours

        :param time_component:
        """
        cls.simpy_time_mapped_to = time_component

    @classmethod
    def map_time_to_steps(cls, day=0, hour=0, minute=0, second=0):

        """match cls.simpy_time_mapped_to:
            case TimeComponent.second:
                steps_per_day = 86400
            case TimeComponent.minute:
                steps_per_day = 1440
            case TimeComponent.hour:
                steps_per_day = 24
            case _:
                steps_per_day = None"""
        if cls.simpy_time_mapped_to == TimeComponent.second:
            steps_per_day = 86400
        elif cls.simpy_time_mapped_to == TimeComponent.minute:
            steps_per_day = 1440
        elif cls.simpy_time_mapped_to == TimeComponent.hour:
            steps_per_day = 24
        else:
            steps_per_day = None

        steps_per_hour = steps_per_day / HOURS_PER_DAY
        steps_per_minute = steps_per_hour / MINUTES_PER_HOUR
        steps_per_seconds = steps_per_minute / SECONDS_PER_MINUTE

        time_in_steps = day * steps_per_day + minute * steps_per_minute + hour * steps_per_hour + second * steps_per_seconds

        return time_in_steps


if __name__ == "__main__":
    locale.setlocale(locale.LC_TIME, "de_DE")
    DateTime.set(datetime(2024, 12, 12, 0, 0, 0))
    print(DateTime.get())

    DateTime.map(TimeComponent.second)
    print(DateTime.get(0.01))

    DateTime.map(TimeComponent.hour)
    print(DateTime.get(25.32))
    print(DateTime.get(25.32, False))
