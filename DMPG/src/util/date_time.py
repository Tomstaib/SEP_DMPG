import locale
from datetime import datetime, timedelta
from enum import Enum
from typing import Union

from src.util.singleton import Singleton
from src.util.helper import round_value, ROUND_DECIMAL_PLACES


class TimeComponent(Enum):
    second = 1
    minute = 60,
    hour = 3600,


class DateTime(Singleton):
    initial_date_time = datetime.now()
    simpy_time_mapped_to = TimeComponent.minute

    @classmethod
    def set(cls, initial_date_time: datetime):
        cls.initial_date_time = initial_date_time

    @classmethod
    def get(cls, time_now: Union[float, int] = 0, from_initial_date: bool = True) -> str:

        match cls.simpy_time_mapped_to:
            case TimeComponent.second:
                delta = timedelta(seconds=time_now)
            case TimeComponent.minute:
                delta = timedelta(minutes=time_now)
            case TimeComponent.hour:
                delta = timedelta(hours=time_now)
            case _:
                delta = timedelta(0)

        if from_initial_date:
            return "".join([f"{round_value(time_now):<{ROUND_DECIMAL_PLACES}}, ", str(delta), ", ",
                            (cls.initial_date_time + delta).strftime('%a %d %b %Y, %H:%M:%S:%f')])
        else:
            return str(delta)

    @classmethod
    def map(cls, time_component: TimeComponent):
        cls.simpy_time_mapped_to = time_component


if __name__ == "__main__":
    locale.setlocale(locale.LC_TIME, "de_DE")
    DateTime.set(datetime(2024, 12, 12, 0, 0, 0))

    print(DateTime.get())
    DateTime.map(TimeComponent.second)
    print(DateTime.get(0.01))
