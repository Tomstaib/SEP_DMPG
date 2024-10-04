import logging

import pandas as pd
from matplotlib import pyplot as plt

from src.util.helper import add_logging_level


class LoggingManager:
    is_loaded = False

    @staticmethod
    def set_logging():
        # https://docs.python.org/3/library/logging.html - see logging levels
        # %(module)s-
        if not LoggingManager.is_loaded:
            add_logging_level('TRACE', logging.DEBUG + 5)  # between DEBUG and INFO
            logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
            logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
            plt.set_loglevel('WARNING')

            pd.set_option('display.max_columns', None)
            pd.set_option('display.max_colwidth', None)
            pd.set_option('max_seq_item', None)
            pd.set_option('display.width', 1000)
            LoggingManager.is_loaded = True
