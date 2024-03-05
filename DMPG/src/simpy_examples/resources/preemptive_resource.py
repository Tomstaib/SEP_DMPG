import simpy


def resource_user(name, env, resource, wait, prio):
    yield env.timeout(wait)
    with resource.request(priority=prio) as req:
        print(f'{name} requesting at {env.now} with priority={prio}')
        yield req
        print(f'{name} got resource at {env.now}')
        try:
            yield env.timeout(3)
        except simpy.Interrupt as interrupt:
            by = interrupt.cause.by
            usage = env.now - interrupt.cause.usage_since
            print(f'{name} got preempted by {by} at {env.now}'
                  f' after {usage}')


def main():
    env = simpy.Environment()
    res = simpy.PreemptiveResource(env, capacity=1)
    env.process(resource_user(1, env, res, wait=0, prio=0))
    env.process(resource_user(2, env, res, wait=1, prio=0))
    env.process(resource_user(3, env, res, wait=2, prio=-1))
    env.run()


if __name__ == "__main__":
    main()
