#! /usr/bin/env python
'''
Reference:
https://simpy.readthedocs.io/en/latest/topical_guides/real-time-simulations.html
'''

import simpy
import time

def example(env):
    start = time.perf_counter()
    yield env.timeout(1)
    end = time.perf_counter()
    print('Duration of one simulation time unit: %.2fs' % (end - start))


import simpy.rt
env = simpy.rt.RealtimeEnvironment(factor=0.1)
proc = env.process(example(env))
env.run(until=proc)
