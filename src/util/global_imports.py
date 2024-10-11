import logging
import random
import pandas as pd
from matplotlib import pyplot as plt
from src.util.singleton import Singleton
from src.util.helper import add_logging_level

RANDOM_SEED = 1
DURATION_WARM_UP = 0
random.seed(RANDOM_SEED)

DAYS_PER_WEEK = 7
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60

ENTITY_PROCESSING_LOG_ENTRY = "{:<120} at {}"

# https://docs.python.org/3/library/logging.html - see logging levels
# %(module)s-
add_logging_level('TRACE', logging.DEBUG + 5)  # between DEBUG and INFO
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
plt.set_loglevel('WARNING')

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('max_seq_item', None)
pd.set_option('display.width', 1000)


# Store detailed stats for each run
class Stats(metaclass=Singleton):
    all_detailed_stats = None


def set_duration_warm_up(value):
    global DURATION_WARM_UP
    DURATION_WARM_UP = value
