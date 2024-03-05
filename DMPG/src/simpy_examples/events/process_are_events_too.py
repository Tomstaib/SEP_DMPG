# https://simpy.readthedocs.io/en/latest/topical_guides/events.html#triggering-events

import simpy


def sub(env):
    yield env.timeout(1)
    return 23               # needs to be a return because (simpy checks if generator) and a yield must return an event


def parent(env):
    ret = yield env.process(sub(env))
    return ret


def main():
    env = simpy.Environment()
    print(env.run(env.process(parent(env))))


if __name__ == "__main__":
    main()
