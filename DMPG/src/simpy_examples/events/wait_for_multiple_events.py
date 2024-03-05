# https://simpy.readthedocs.io/en/latest/topical_guides/events.html#waiting-for-multiple-events-at-once

import simpy


def test_condition(env):
    t1, t2 = env.timeout(1, value='spam'), env.timeout(2, value='eggs')
    ret = yield t1 | t2
    print(ret)
    assert ret == {t1: 'spam'}

    t1, t2 = env.timeout(1, value='spam'), env.timeout(2, value='eggs')
    ret = yield t1 & t2
    print(ret)
    assert ret == {t1: 'spam', t2: 'eggs'}

    # You can also concatenate & and |
    e1, e2, e3 = [env.timeout(i) for i in range(3)]
    yield (e1 | e2) & e3
    print(ret)
    assert all(e.processed for e in [e1, e2, e3])


if __name__ == "__main__":
    env = simpy.Environment()
    proc = env.process(test_condition(env))
    env.run()
