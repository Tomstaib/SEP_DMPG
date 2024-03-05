import simpy


def car(env: simpy.Environment):
    while True:
        print(f'Start parking at {env.now:f}')
        parking_duration = 5.1
        yield env.timeout(parking_duration)

        print(f'Start driving at {env.now:f}')
        trip_duration = 2.678
        yield env.timeout(trip_duration)


def main():
    env = simpy.Environment()
    env.process(car(env))
    env.run(until=15.2123)


if __name__ == "__main__":
    main()
