import simpy
import logging


class Car(object):
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.action = env.process(self.run())

    def run(self):
        while True:
            logging.info(f'Start charging {self.env.now:d}')
            charge_duration = 5
            logging.debug(f"Active process: {self.env.active_process}")
            try:
                yield self.env.process(self.charge(charge_duration))
            except simpy.Interrupt:
                logging.info("Charging was interrupted.")

            logging.info(f'Start driving at {self.env.now:d}')
            trip_duration = 2
            yield self.env.timeout(trip_duration)

    def charge(self, duration):
        logging.debug(f"processing: {self.env.active_process}")
        yield self.env.timeout(duration)


def driver(env, car):
    yield env.timeout(5)
    car.action.interrupt()


def main():
    env = simpy.Environment()
    car = Car(env)
    env.process(driver(env, car))
    env.run(until=15)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    main()
