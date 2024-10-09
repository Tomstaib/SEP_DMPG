if 'seconds_previous_computations' not in globals():
    seconds_previous_computations = 0

import time
from datetime import timedelta


def start_timer():
    return time.time()

def end_timer(start_time):
    return time.time() - start_time

def get_time_statistics(start_time):
    return end_timer(start_time)

def get_percentage_and_computing_times(computing_time_start, i, num_replications):
    global seconds_previous_computations

    if 'seconds_previous_computations' not in globals():
        seconds_previous_computations = 0

    seconds_computed = time.time() - computing_time_start
    seconds_computed_iteration = seconds_computed - seconds_previous_computations
    seconds_previous_computations = seconds_computed

    percentage = round((i + 1) / num_replications * 100)
    total_seconds_to_complete = seconds_computed / (percentage / 100)

    return (f"{percentage:>3}%",
            f"[time computed] {str(timedelta(seconds=seconds_computed)):<15}",
            f"[time to complete] {str(timedelta(seconds=total_seconds_to_complete - seconds_computed)):<15}",
            f"[time prediction] {str(timedelta(seconds=total_seconds_to_complete)):<15}",
            f"[time per iteration] {str(timedelta(seconds=seconds_computed_iteration)):<15}")

def print_stats(i, num_replications, start, tenth_percentage):
    if tenth_percentage == 0 or (i + 1) % tenth_percentage == 0:
        ct = get_percentage_and_computing_times(start, i, num_replications)
        print(f"{ct[0]} replication {i + 1}/{num_replications}\t{ct[1]}\t{ct[2]}\t{ct[3]}\t{ct[4]}")
        if (i + 1) % 10 == 0 or i + 1 == num_replications:
            print(f"Zwischenstand nach {i + 1} Replikationen:")
            print(f"Voraussichtliche Gesamtlaufzeit für alle Replikationen: {ct[3]}")
