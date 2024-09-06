import json
import os
import requests
import logging

URL = 'https://131.173.65.76:5000/receive_runtime_prediction' #Webserver wird hier angesprochen


def send_progress_to_server(ct, i, step, num_replications):
    data = save_progress(ct, i, step, num_replications)
    response = requests.post(URL, json=data, verify=False)

    if response.status_code != 200:
        logging.info(f"Error while sending Runtime-Prediction: {response.status_code}")
    else:
        logging.info("Runtime prediction successfully sent to webserver")


def save_progress(ct, i, step, num_replications):
    progress_data = {
        "percentage": ct[0].replace(" ", ""),
        "time_computed": ct[1].replace("[time computed] ", "").strip(),
        "time_to_complete": ct[2].replace("[time to complete] ", "").strip(),
        "time_prediction": ct[3].replace("[time prediction] ", "").strip(),
        "time_per_iteration": ct[4].replace("[time per iteration] ", "").strip(),
        "current_iteration": i + 1,
        "total_iterations": num_replications
    }
    return progress_data
