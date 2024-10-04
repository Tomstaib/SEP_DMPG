import random

from src.util.singleton import Singleton
from src.util.logging_manager import LoggingManager

RANDOM_SEED = 1
DURATION_WARM_UP = 0
random.seed(RANDOM_SEED)

DAYS_PER_WEEK = 7
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60

ENTITY_PROCESSING_LOG_ENTRY = "{:<120} at {}"

LoggingManager.set_logging()


# Store detailed stats for each run
class Stats(Singleton):
    all_detailed_stats = None


def set_duration_warm_up(value):
    global DURATION_WARM_UP
    DURATION_WARM_UP = value
