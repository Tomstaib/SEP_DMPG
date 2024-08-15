import os

from models.model_pcb import setup_model_pcb
from models.model_pcb_with_breakdowns import setup_model_pcb_with_breakdowns
from models.model_pcb_with_arrival_table import setup_model_pcb_with_arrival_table
from src.util.simulations import run_replications, run_simulation
from src.util.visualization import histogram, boxplot, scatterplot, violinplot, visualize_system
import logging
import matplotlib.pyplot as plt


def main():
    print(os.getcwd())
    run_simulation(model=setup_model_pcb, minutes=900)
    visualize_system()

    run_simulation(model=setup_model_pcb_with_breakdowns, minutes=900)

    run_simulation(model=setup_model_pcb_with_arrival_table, minutes=900)

    run_replications(model=setup_model_pcb, minutes=900, num_replications=1000, multiprocessing=False)
    histogram('Sink', 'AvgTimeInSystem')
    histogram('Server', 'AvgTimeProcessing')
    boxplot('Server', 'TotalTimeProcessing')
    scatterplot('Sink', 'AvgTimeInSystem', 'NumberEntered')
    violinplot('Server', 'ScheduledUtilization')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(module)s-%(levelname)s: %(message)s')
    logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
    plt.set_loglevel('WARNING')

    main()
