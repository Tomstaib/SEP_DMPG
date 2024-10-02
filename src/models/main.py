from models.model_pcb import setup_model_pcb
from models.model_pcb_with_arrival_table import setup_model_pcb_with_arrival_table
from src.util.simulations import run_replications, run_simulation
import logging
import matplotlib.pyplot as plt
from datetime import datetime


def main():
    # run_simulation(model=setup_model_pcb, minutes=900)
    # visualize_system()
    # run_simulation(model=setup_model_pcb_with_breakdowns, minutes=900)

    run_simulation(model=setup_model_pcb_with_arrival_table, minutes=900)
    start_time = datetime.now()
    run_replications(model=setup_model_pcb, minutes=5250000, num_replications=100, multiprocessing=True)
    finish = datetime.now()
    time_elapsed = finish - start_time
    print(time_elapsed)
    # histogram('Sink', 'AvgTimeInSystem')
    # histogram('Server', 'AvgTimeProcessing')
    # boxplot('Server', 'TotalTimeProcessing')
    # scatterplot('Sink', 'AvgTimeInSystem', 'NumberEntered')
    # violinplot('Server', 'ScheduledUtilization')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(module)s-%(levelname)s: %(message)s')
    logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
    plt.set_loglevel('WARNING')

    """monitoring_thread = threading.Thread(target=monitor_resources, args=(10,))
    monitoring_thread.daemon = True  # Ensures the thread stops when the main program exits
    monitoring_thread.start()"""

    main()
