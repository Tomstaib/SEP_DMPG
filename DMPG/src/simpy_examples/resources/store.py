# https://simpy.readthedocs.io/en/latest/topical_guides/resources.html#stores
import simpy


def producer(env, store):
    for i in range(100):
        yield env.timeout(5)
        yield store.put(f'spam {i}')
        print(f'Produced spam at {env.now}')


def consumer(name, env, store):
    while True:
        yield env.timeout(1)
        print(name, 'requesting spam at', env.now)
        item = yield store.get()
        print(name, 'got', item, 'at', env.now)


def main():
    env = simpy.Environment()
    store = simpy.Store(env, capacity=2)
    env.process(producer(env, store))
    [env.process(consumer(i, env, store)) for i in range(2)]
    env.run(10)


if __name__ == "__main__":
    main()
