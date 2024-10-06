import psutil
import time

def monitor_resources(interval: int = 30, max_iterations: int = None):
    """
    Monitor resource usage rudimentary based on psutil. The usages will be printed in an interval.

    :param interval: Interval in which the monitoring should be done in seconds.
    :param max_iterations: Optional. Number of iterations to run the monitoring loop. If None, the loop will run indefinitely. For test purposes only.
    """
    iterations = 0
    try:
        while True:
            # Monitor CPU and RAM
            cpu_percent = psutil.cpu_percent(interval=interval, percpu=True)
            mem = psutil.virtual_memory()
            print(f"CPU Usage: {cpu_percent}%, RAM Usage: {mem.percent}% (Used: {mem.used / (1024 ** 3):.2f} GB, Total: {mem.total / (1024 ** 3):.2f} GB)")

            iterations += 1
            if max_iterations is not None and iterations == max_iterations:
                break

            time.sleep(interval)
    except KeyboardInterrupt:
        print("Monitoring stopped.")
