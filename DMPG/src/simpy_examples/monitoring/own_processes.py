import simpy


def test_process(env, data):
    val = 0
    for i in range(5):
        val += env.now
        data.append(val)  # Collect data
        yield env.timeout(1)


def main():
    data = []  # This list will hold all collected data
    env = simpy.Environment()
    p = env.process(test_process(env, data))
    env.run(p)
    print('Collected', data)  # Lets see what we got


if __name__ == "__main__":
    main()
