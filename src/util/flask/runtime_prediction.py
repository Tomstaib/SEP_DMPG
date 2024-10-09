from typing import Optional
import requests
import logging
import getpass
from requests import Response

URL = 'https://131.173.65.76:5000/receive_runtime_prediction'
"""URL to send the runtime prediction to."""


def send_progress_to_server(ct: (str, str, str, str, str), i: int, num_replications: int):
    """
    Send the simulation progress to the server.

    :params ct: A tuple containing formatted strings for percentage completion and time metrics.
    :params i: The current iteration number.
    :params num_replications: The total number of replications.

    See also:
        - [save_progress](../util/flask/runtime_prediction.html#save_progress): Save Progress in a dictionary.
    """
    user: str = getpass.getuser()

    data: dict[str, int] = save_progress(ct, i, num_replications)

    if data is None:
        logging.error("No data to send. Progress data creation failed.")
        return

    try:
        # Pass current user as URL-parameter
        response: Response = requests.post(URL, json=data, params={'user': user}, verify=False)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        logging.info(f"Runtime prediction successfully sent to webserver by user {user}")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while sending Runtime-Prediction: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred while sending Runtime-Prediction: {req_err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def save_progress(ct: (str, str, str, str, str), i: int, num_replications: int) -> Optional[dict[str, int]]:
    """
    Save the current progress as a dictionary.

    :params ct: A tuple containing formatted strings for percentage completion and time metrics.
    :params i: The current iteration number.
    :params num_replications: The total number of replications.

    :return: A dictionary containing the data.
    """
    try:
        progress_data: dict[str, int] = {
            "percentage": ct[0].replace(" ", ""),
            "time_computed": ct[1].replace("[time computed] ", "").strip(),
            "time_to_complete": ct[2].replace("[time to complete] ", "").strip(),
            "time_prediction": ct[3].replace("[time prediction] ", "").strip(),
            "time_per_iteration": ct[4].replace("[time per iteration] ", "").strip(),
            "current_iteration": i + 1,
            "total_iterations": num_replications
        }
    except IndexError as e:
        logging.error("Error accessing ct elements: %s", e)
        return None
    except AttributeError as e:
        logging.error("Error processing string attributes: %s", e)
        return None
    except Exception as e:
        logging.error("Unknown error: %s", e)
        return None
    return progress_data
