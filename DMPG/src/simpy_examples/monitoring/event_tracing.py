from functools import partial, wraps
import simpy


def trace(env, callback):
    """Replace the ``step()`` method of *env* with a tracing function
    that calls *callbacks* with an events time, priority, ID and its
    instance just before it is processed.

    """
    def get_wrapper(env_step, callback):
        """Generate the wrapper for env.step()."""
        @wraps(env_step)
        def tracing_step():
            """Call *callback* for the next event if one exist before
            calling ``env.step()``."""
            if len(env._queue):
                t, prio, eid, event = env._queue[0]
                callback(t, prio, eid, event)
            return env_step()
        return tracing_step

    env.step = get_wrapper(env.step, callback)


def test_process(env):
    yield env.timeout(1)


def main():
    def monitor(data, t, prio, eid, event: simpy.Event):
        data.append((t, eid, type(event), event.triggered))

    data = []
    # Bind *data* as first argument to monitor()
    # see https://docs.python.org/3/library/functools.html#functools.partial

    monitor = partial(monitor, data)
    env = simpy.Environment()
    trace(env, monitor)
    p = env.process(test_process(env))
    env.run(until=p)

    for d in data:
        print(d)


if __name__ == "__main__":
    main()
