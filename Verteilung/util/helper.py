import logging
from typing import Tuple, Callable, Union


ROUND_DECIMAL_PLACES = 4


def get_value_from_distribution_with_parameters(dwp: Tuple[Callable[..., float]]):
    distribution, parameters = dwp[0], dwp[1:]
    return distribution(*parameters)


def validate_probabilities(component):
    specified_probs = [prob for _, prob in component.next_component if prob is not None]
    unspecified_probs_count = len(component.next_component) - len(specified_probs)
    total_specified = sum(specified_probs)

    if total_specified > 100:
        raise ValueError(f"Total probability exceeds 100% for source {component.name}")

    if unspecified_probs_count > 0:
        remaining_prob = (100 - total_specified) / unspecified_probs_count
        component.next_component = [(server, prob if prob is not None else remaining_prob) for server, prob in
                                    component.next_component]

    if sum(prob for _, prob in component.next_component) != 100:
        raise ValueError(f"Total probability does not sum up to 100% for source {component.name}")


def create_connection_cache(component):

    cumulative_probability = 0
    for next_server, probability in component.next_component:
        cumulative_probability += probability

        component.connection_cache[cumulative_probability] = next_server


import logging

def add_logging_level(level_name, level_num, method_name=None):
    """
    Dynamically add a new logging level to the logging module.

    :param level_name: Name of the new logging level.
    :param level_num: Numeric value of the logging level.
    :param method_name: Optional method name for the new logging level.
    """
    method_name = method_name or level_name.lower()

    if hasattr(logging, level_name):
        logging.warning(f"Logging level '{level_name}' is already defined.")
        return

    if hasattr(logging, method_name):
        logging.warning(f"Method '{method_name}' is already defined in logging.")
        return

    def log_for_level(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def log_to_root(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    setattr(logging.getLoggerClass(), method_name, log_for_level)
    setattr(logging, method_name, log_to_root)



def round_value(val: Union[int, float]):
    return round(val, ROUND_DECIMAL_PLACES) if isinstance(val, float) else val