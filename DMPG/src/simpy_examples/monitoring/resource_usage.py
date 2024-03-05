from functools import partial, wraps
import simpy


def patch_resource(resource, pre=None, post=None):
    """Patch *resource* so that it calls the callable *pre* before each
    put/get/request/release operation and the callable *post* after each
    operation.  The only argument to these functions is the resource
    instance.

    """
    def get_wrapper(func):
        # Generate a wrapper for put/get/request/release
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This is the actual wrapper
            # Call "pre" callback
            if pre:
                pre(resource)

            # Perform actual operation
            ret = func(*args, **kwargs)

            # Call "post" callback
            if post:
                post(resource)

            return ret
        return wrapper

    # Replace the original operations with our wrapper
    for name in ['put', 'get', 'request', 'release']:
        if hasattr(resource, name):
            setattr(resource, name, get_wrapper(getattr(resource, name)))


def test_process(env, res):
    with res.request() as req:
        yield req
        yield env.timeout(5)


def main():

    def monitor(data, resource):
        """This is our monitoring callback."""
        item = (
            resource._env.now,      # current simulation time
            resource.count,         # number of users
            len(resource.queue),    # number of queued processes
        )
        data.append(item)

    env = simpy.Environment()
    res = simpy.Resource(env, capacity=1)
    data = []
    # Bind *data* as first argument to monitor()
    # see https://docs.python.org/3/library/functools.html#functools.partial
    m = partial(monitor, data)
    patch_resource(res, pre=m, post=m)  # Patches (only) this resource instance
    env.process(test_process(env, res))
    p2 = env.process(test_process(env, res))

    env.run(p2)
    # time, current users, len queue
    print(data)


if __name__ == "__main__":
    main()
