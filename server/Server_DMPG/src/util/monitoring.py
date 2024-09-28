import random

import psutil
import time

def monitor_resources(interval=30):
    try:
        while True:
            # Monitor CPU and RAM
            cpu_percent = psutil.cpu_percent(interval=interval, percpu=True)
            mem = psutil.virtual_memory()
            print(f"CPU Usage: {cpu_percent}%, RAM Usage: {mem.percent}% (Used: {mem.used / (1024 ** 3):.2f} GB, Total: {mem.total / (1024 ** 3):.2f} GB)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Monitoring stopped.")


def randomized_main() -> (int,int):
    random_minutes: int = random.randint(52500, 52500000)
    random_replications: int = random.randint(10, 500)
    return random_minutes, random_replications
