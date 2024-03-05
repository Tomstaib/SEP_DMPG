import simpy
import logging

bcs = None


class Car(object):
    def __init__(self, env: simpy.Environment, name: str):
        self.env = env
        self.name = name
        self.action = env.process(self.run())

    def run(self):
        global bcs

        while True:

            with bcs.request() as req:
                logging.info(f'{self.name} waiting to be charged at {self.env.now:d}')
                yield req

                logging.info(f'{self.name} starts charging at {self.env.now:d}')
                charge_duration = 5
                logging.debug(f"Active process: {self.env.active_process}")
                try:
                    yield self.env.process(self.charge(charge_duration))
                except simpy.Interrupt:
                    logging.info("{self.name} charging was interrupted.")

            logging.info(f'{self.name} start driving at {self.env.now:d}')
            trip_duration = 2
            yield self.env.timeout(trip_duration)

    def charge(self, duration):
        logging.debug(f"processing: {self.env.active_process}")
        yield self.env.timeout(duration)


def main():
    env = simpy.Environment()
    global bcs
    bcs = simpy.Resource(env, capacity=2)
    for i in range(4):
        Car(env, 'car' + str(i))
    env.run(until=15)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    main()
