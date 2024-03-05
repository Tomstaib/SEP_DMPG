# https://simpy.readthedocs.io/en/latest/topical_guides/resources.html#containers
import simpy


class GasStation:
    def __init__(self, env):
        self.fuel_dispensers = simpy.Resource(env, capacity=2)
        self.gas_tank = simpy.Container(env, init=100, capacity=1000)
        self.mon_proc = env.process(self.monitor_tank(env))

    def monitor_tank(self, env):
        while True:
            if self.gas_tank.level < 100:
                print(f'Calling tanker at {env.now}')
                env.process(tanker(env, self))
            yield env.timeout(15)


def tanker(env, gas_station):
    yield env.timeout(10)  # Need 10 Minutes to arrive
    print(f'Tanker arriving at {env.now}')
    amount = gas_station.gas_tank.capacity - gas_station.gas_tank.level
    print(f"filling {amount - 0.05}")
    yield gas_station.gas_tank.put(amount - 0.05)


def car(name, env, gas_station):
    print(f'Car {name} arriving at {env.now}')
    with gas_station.fuel_dispensers.request() as req:
        yield req
        print(f'Car {name} starts refueling at {env.now}')
        yield gas_station.gas_tank.get(40)
        yield env.timeout(5)
        print(f'Car {name} done refueling at {env.now}')


def car_generator(env, gas_station):
    for i in range(10):
        env.process(car(i, env, gas_station))
        yield env.timeout(5)


def main():
    env = simpy.Environment()
    gas_station = GasStation(env)
    env.process(car_generator(env, gas_station))
    env.run(100)
    print(f"{gas_station.gas_tank.level}")


if __name__ == "__main__":
    main()
