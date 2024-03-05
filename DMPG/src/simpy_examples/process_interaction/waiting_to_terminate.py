# https://simpy.readthedocs.io/en/latest/topical_guides/process_interaction.html#waiting-for-another-process-to-terminate

from random import randint
import simpy


class EV:
    def __init__(self, env):
        self.env = env
        self.drive_proc = env.process(self.drive(env))

    def drive(self, env):
        while True:
            # Drive for 20-40 min
            yield env.timeout(randint(20, 40))

            # Park for 1–6 hours
            print('Start parking at', env.now)
            charging = env.process(self.bat_ctrl(env))
            parking = env.timeout(randint(60, 360))

            yield charging & parking
            print('Stop parking at', env.now)

    @staticmethod
    def bat_ctrl(env):
        print('Bat. ctrl. started at', env.now)
        # Intelligent charging behavior here …
        yield env.timeout(randint(30, 90))
        print('Bat. ctrl. done at', env.now)


def main():
    env = simpy.Environment()
    EV(env)
    env.run(until=310)


if __name__ == "__main__":
    main()
