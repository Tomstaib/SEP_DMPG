import logging
from typing import Tuple, Callable, Union


ROUND_DECIMAL_PLACES = 4


def get_value_from_distribution_with_parameters(dwp: Tuple[Callable[..., float]], unit: str = 'seconds'):
    """
    Get a value from a distribution with parameters.

    :param dwp: Tuple of distribution function and parameters
    :param unit: Time unti of the distribution. Default value is simulation steps

    :return: Value from the distribution
    """
    from src.util.date_time import DateTime

    distribution, parameters = dwp[0], dwp[1:]
    value = distribution(*parameters)
    match unit:
        case 'second':
            time_as_step = DateTime.map_time_to_steps(second=value)
        case 'minute':
            time_as_step = DateTime.map_time_to_steps(minute=value)
        case 'hour':
            time_as_step = DateTime.map_time_to_steps(hour=value)
        case 'day':
            time_as_step = DateTime.map_time_to_steps(day=value)
        case _:
            time_as_step = value

    return time_as_step


def validate_probabilities(component) -> None:
    """
    Validate probabilities for the next component of a source.
    If the probabilities are not specified, they are divided equally among the unspecified components.

    :param component:
    """
    # Changed to use connections instead of next components because next components always are connections
    specified_probs = []
    for connection in component.connections:
        if component.connections[connection].probability is not None:
            specified_probs.append(component.connections[connection].probability)
    unspecified_probs_count = len(component.connections) - len(specified_probs)
    total_specified = sum(specified_probs)

    if total_specified > 100:
        raise ValueError(f"Total probability exceeds 100% for source {component.name}")

    if unspecified_probs_count > 0:
        remaining_prob = (100 - total_specified) / unspecified_probs_count
        for connection_key, connection_value in component.connections.items():
            if connection_value.probability is None:
                connection_value.probability = remaining_prob

    total_probability = sum(component.connections[connection].probability for connection in component.connections)
    if round(total_probability, 0) != 100:
        raise ValueError(f"Total probability {total_probability:0.3f} does not sum up to 100% for {component.name}")


def create_connection_cache(component) -> None:
    """
    Create a cache for a given component which cumulates the probability of all given servers.
    :param component:
    """
    # now works with connections instead of next components because next components always are connections
    cumulative_probability = 0
    for connection in component.connections:
        cumulative_probability += component.connections[connection].probability

        component.connection_cache[cumulative_probability] = component.connections[connection]


def add_logging_level(level_name, level_num, method_name=None) -> None:
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

    :param level_name: The name of the logging level to add
    :param level_num: The number of the logging level to add
    :param method_name: The name of the logging method. Default = None
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
    """Rounds value

    :param val: value
    :return: rounded value either int or float
    """
    return round(val, ROUND_DECIMAL_PLACES) if isinstance(val, float) else val
