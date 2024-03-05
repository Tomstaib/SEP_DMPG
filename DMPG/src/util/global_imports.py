import logging
import random
from matplotlib import pyplot as plt

from src.util.singleton import Singleton
from src.util.helper import add_logging_level

RANDOM_SEED = 1
random.seed(RANDOM_SEED)

ENTITY_PROCESSING_LOG_ENTRY = "{:<120} at {}"

# https://docs.python.org/3/library/logging.html - see logging levels
# %(module)s-
add_logging_level('TRACE', logging.DEBUG + 5)  # between DEBUG and INFO
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
plt.set_loglevel('WARNING')


# Store detailed stats for each run
class Stats(Singleton):
    all_detailed_stats = None
