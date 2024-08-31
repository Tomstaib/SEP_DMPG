from models.model_pcb import setup_model_pcb
from models.model_pcb_with_breakdowns import setup_model_pcb_with_breakdowns
from models.model_pcb_with_arrival_table import setup_model_pcb_with_arrival_table
from src.util.simulations import run_replications, run_simulation
from src.util.visualization import histogram, boxplot, scatterplot, violinplot, visualize_system
import logging
import matplotlib.pyplot as plt
from datetime import datetime
import threading
from src.util.monitoring import monitor_resources, randomized_main


def main():
    # run_simulation(model=setup_model_pcb, minutes=900)
    # visualize_system()

    # run_simulation(model=setup_model_pcb_with_breakdowns, minutes=900)

    # run_simulation(model=setup_model_pcb_with_arrival_table, minutes=900)
    with open('optimized_DMPG.csv', 'a') as f:
        for i in range(1000):
            random_minutes, random_replications = randomized_main()

            now = datetime.now()

            run_replications(model=setup_model_pcb, minutes=random_minutes, num_replications=random_replications, multiprocessing=True)
            finish = datetime.now()
            time_elapsed = finish - now

            f.write(f"{time_elapsed.total_seconds()}, {(random_minutes/60)}, {random_replications}\n")
    # histogram('Sink', 'AvgTimeInSystem')
    # histogram('Server', 'AvgTimeProcessing')
    # boxplot('Server', 'TotalTimeProcessing')
    # scatterplot('Sink', 'AvgTimeInSystem', 'NumberEntered')
    # violinplot('Server', 'ScheduledUtilization')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(module)s-%(levelname)s: %(message)s')
    logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
    plt.set_loglevel('WARNING')

    """monitoring_thread = threading.Thread(target=monitor_resources, args=(30,))
    monitoring_thread.daemon = True  # Ensures the thread stops when the main program exits
    monitoring_thread.start()"""

    main()
