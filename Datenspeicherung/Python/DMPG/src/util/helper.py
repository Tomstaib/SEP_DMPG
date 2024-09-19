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


def add_logging_level(level_name, level_num, method_name=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present
    """
    if not method_name:
        method_name = level_name.lower()

    if hasattr(logging, level_name):
        raise AttributeError('{} already defined in logging module'.format(level_name))
    if hasattr(logging, method_name):
        raise AttributeError('{} already defined in logging module'.format(method_name))
    if hasattr(logging.getLoggerClass(), method_name):
        raise AttributeError('{} already defined in logger class'.format(method_name))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    setattr(logging.getLoggerClass(), method_name, logForLevel)
    setattr(logging, method_name, logToRoot)


def round_value(val: Union[int, float]):
    return round(val, ROUND_DECIMAL_PLACES) if isinstance(val, float) else val
