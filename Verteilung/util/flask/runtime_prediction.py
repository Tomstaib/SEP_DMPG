import requests
import logging


URL = 'https://131.173.65.76:5000/receive_runtime_prediction'


# MockResponse class, which creates a mock object and includes the raise_for_status() method
class MockResponse:
    def __init__(self, status_code):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"Mock HTTP error with status code {self.status_code}")


def send_progress_to_server(ct, i, step, num_replications):
    data = save_progress(ct, i, step, num_replications)
    try:
        ''' 
        response = requests.post(URL, json=data, verify=False)
        '''
        response = MockResponse(200)  # mock HTTP response with status code 200 (successful)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        logging.info("Runtime prediction successfully sent to webserver")
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