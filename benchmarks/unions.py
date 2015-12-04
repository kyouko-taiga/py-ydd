# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

import argparse
import random
import sys
import time

from functools import reduce
from operator import or_

from ydd.ydd import Engine


def benchmark(nb_singletons=50, nb_elements=100):
    # Initialization (not measured).
    n = nb_singletons
    m = nb_elements

    engine = Engine()
    singletons = [[int(random.random() * m) for _ in range(m)] for _ in range(n)]

    # Benchmark tests.
    benchmark_start = time.time()
    singleton_start = time.time()

    diagrams = [engine.make_one(singleton) for singleton in singletons]

    singleton_time = time.time() - singleton_start
    union_start = time.time()

    reduce(or_, diagrams)

    union_time = time.time() - union_start
    benchmark_time = time.time() - benchmark_start

    # Print results.
    print('{:<20} {}'.format('Total time:', benchmark_time))
    print('{:<20} {}'.format('Create singletons:', singleton_time))
    print('{:<20} {}'.format('Compute unions:', union_time))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--singletons', dest='singletons', action='store', default=40, type=int,
        help='The number of singletons to create (default: 50).')
    parser.add_argument(
        '-e', '--elements', dest='elements', action='store', default=100, type=int,
        help='The (maximum) number of elements in each singleton (default: 100).')

    args = parser.parse_args()
    benchmark(args.singletons, args.elements)
