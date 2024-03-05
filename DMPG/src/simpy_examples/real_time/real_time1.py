# https://simpy.readthedocs.io/en/latest/topical_guides/real-time-simulations.html

import time
import simpy


def example(env):
    start = time.perf_counter()
    # time.sleep(3) - breaking real time constraint
    yield env.timeout(1)
    end = time.perf_counter()
    print('Duration of one simulation time unit: %.2fs' % (end - start))


def main():
    env = simpy.Environment()                                   # normal environment
    proc = env.process(example(env))
    env.run(until=proc)

    env = simpy.rt.RealtimeEnvironment(factor=1, strict=True)   # real time environment
    proc = env.process(example(env))
    env.run(until=proc)


if __name__ == "__main__":
    main()
