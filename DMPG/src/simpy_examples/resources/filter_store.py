from collections import namedtuple
import simpy


def user(name: int, env: simpy.Environment, ms: simpy.FilterStore, size: int):
    machine = yield ms.get(lambda m: m.size == size)
    print(name, 'got', machine, 'at', env.now)
    yield env.timeout(machine.duration)
    yield ms.put(machine)
    print(name, 'released', machine, 'at', env.now)


def main():
    machine = namedtuple('Machine', 'size, duration')
    m1 = machine(1, 2)  # Small and slow
    m2 = machine(2, 1)  # Big and fast
    env = simpy.Environment()
    machine_shop = simpy.FilterStore(env, capacity=2)
    machine_shop.items = [m1, m2]  # Pre-populate the machine shop
    [env.process(user(i, env, machine_shop, (i % 2) + 1)) for i in range(3)]
    env.run()


if __name__ == "__main__":
    main()
