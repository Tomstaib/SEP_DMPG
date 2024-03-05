# https://simpy.readthedocs.io/en/latest/topical_guides/events.html#example-usages-for-event

import simpy


class School:
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.class_ends = env.event()   # create a new event
        self.pupil_procs = [env.process(self.pupil()) for _ in range(3)]
        self.bell_proc = env.process(self.bell())

    def bell(self):
        for _ in range(2):
            yield self.env.timeout(45)
            self.class_ends.succeed()           # set current class event to be processed
            # self.class_ends.fail(simpy.exceptions.SimPyException())
            self.class_ends = self.env.event()  # create a new (not processed) event
            print()

    def pupil(self):
        for _ in range(2):
            print(r' \o/', end='')
            yield self.class_ends           # return to wait on another event


def main():
    env = simpy.Environment()
    School(env)
    env.run()


if __name__ == "__main__":
    main()
