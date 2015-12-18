# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

import argparse
import importlib
import sys
import time

from petrinet import PetriNet


def load_class(class_path):
    class_data = class_path.split(".")
    module_path = ".".join(class_data[:-1])
    class_name = class_data[-1]

    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def benchmark(pnml, engine, recursion_limit=None):
    # Set the recursion limit.
    if recursion_limit:
        previous_recursion_limit = sys.getrecurstionlimit
        sys.setrecursionlimit(recursion_limit)

    # Parse the pnml file to generate.
    pns = PetriNet.from_pnml(engine, pnml)
    print('%i Petri Net(s) found in the pnml file.' % len(pns))

    # Benchmark tests.
    for id_, pn in pns.items():
        print('Generate the state space for "%s".' % id_)
        start = time.time()
        state_space = pn.state_space()
        elapsed = time.time() - start
        print('\t%i state(s), computed in %f[s]' % (len(state_space), elapsed))

    # Reset the recursion limit.
    if recursion_limit:
        sys.setrecursionlimit(previous_recursion_limit)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pnml', metavar='pnml', help='The filename of the PNML file to parse.')
    parser.add_argument(
        '-r', '--recursion-limit', dest='recursion', metavar='N', type=int,
        help="Override Python's default recursion limit.")
    parser.add_argument(
        '--engine', dest='engine', default='ydd.engines.default.DefaultEngine',
        help=(
            "The path of the engine class to be used to handle nodes "
            "(default: ydd.engines.default.DefaultEngine)."
            ))

    args = parser.parse_args()

    engine_class = load_class(args.engine)
    engine = engine_class()

    benchmark(args.pnml, engine, args.recursion)
