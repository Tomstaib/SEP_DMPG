import requests
import logging
import getpass  # Zum Abrufen des aktuellen Benutzers

URL = 'https://131.173.65.76:5000/receive_runtime_prediction'


def send_progress_to_server(ct, i, step, num_replications):
    # Hole den aktuellen Systembenutzer
    user = getpass.getuser()

    data = save_progress(ct, i, step, num_replications)
    if data is None:
        logging.error("No data to send. Progress data creation failed.")
        return

    try:
        # Übergib den aktuellen Benutzer als URL-Parameter
        response = requests.post(URL, json=data, params={'user': user}, verify=False)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        logging.info(f"Runtime prediction successfully sent to webserver by user {user}")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while sending Runtime-Prediction: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred while sending Runtime-Prediction: {req_err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def save_progress(ct, i, step, num_replications):
    try:
        progress_data = {
            "percentage": ct[0].replace(" ", ""),
            "time_computed": ct[1].replace("[time computed] ", "").strip(),
            "time_to_complete": ct[2].replace("[time to complete] ", "").strip(),
            "time_prediction": ct[3].replace("[time prediction] ", "").strip(),
            "time_per_iteration": ct[4].replace("[time per iteration] ", "").strip(),
            "current_iteration": i + 1,
            "total_iterations": num_replications
        }
    except IndexError as e:
        # Handle index errors
        logging.error("Error accessing ct elements: %s", e)
        return None
    except AttributeError as e:
        # Handle attribute errors
        logging.error("Error processing string attributes: %s", e)
        return None
    except Exception as e:
        # Handle all other exceptions
        logging.error("Unknown error: %s", e)
        return None
    return progress_data

