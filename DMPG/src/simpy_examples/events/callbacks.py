# https://simpy.readthedocs.io/en/latest/topical_guides/events.html#adding-callbacks-to-an-event

import simpy


def my_callback(event):
    print('Called back from', event)


def main():
    env = simpy.Environment()

    # create event and attach callback
    event = env.event()
    event.callbacks.append(my_callback)
    print(event.callbacks)

    # indirectly trigger the event by marking it as processed
    event.succeed()
    env.step()       # process next event


if __name__ == "__main__":
    main()
