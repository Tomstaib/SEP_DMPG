# https://simpy.readthedocs.io/en/latest/topical_guides/resources.html#the-basic-concept-of-resources
import simpy


def print_stats(res):
    print(f"{res.count} of {res.capacity} slots are allocated.")
    print(f"  Users: {res.users}")
    print(f"  Queued events: {res.queue}")


def resource_user(env: simpy.Environment, user: str, resource):
    with resource.request() as request:  # Generate a request event
        print_stats(resource)
        print(f"{user} waiting for resource {env.now}")
        yield request                 # Wait for access
        print_stats(resource)
        print(f"{user} resource granted & processing {env.now}")
        print_stats(resource)
        yield env.timeout(2)          # Do something
        print(f"{user} resource released & processing {env.now}")
        resource.release(request)     # Release the resource


def main():
    env = simpy.Environment()
    res = simpy.Resource(env, capacity=1)
    env.process(resource_user(env, "user1", res))
    env.process(resource_user(env, "user2", res))
    env.process(resource_user(env, "user3", res))
    env.run()


if __name__ == "__main__":
    main()
