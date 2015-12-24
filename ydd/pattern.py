# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

from functools import reduce
from operator import and_, or_


class Symbol(object):

    def __init__(self, value, enabled=True):
        self.value = value
        self.enabled = enabled

    def __invert__(self):
        return Symbol(self.value, not self.enabled)

    def __lt__(self, other):
        if self.value == other.value:
            return other.enabled and not self.enabled
        else:
            return self.value < other.value

    def __eq__(self, other):
        return (self.value == other.value) and (self.enabled == other.enabled)

    def __hash__(self):
        return hash((self.value, self.enabled))

    def __str__(self):
        return ('~' if not self.enabled else '') + str(self.value)

    def __repr__(self):
        return ('~' if not self.enabled else '') + repr(self.value)


class Pattern(object):

    def __init__(self, minterms=None):
        self.minterms = minterms or make_minterm()

    def __invert__(self):
        if len(self.minterms) <= 1:
            mt = next(iter(self.minterms))
            return reduce(or_, (Pattern(make_minterm(~Symbol(sym))) for sym in mt))
        else:
            return reduce(and_, (~Pattern(set([mt])) for mt in self.minterms))

    def __or__(self, other):
        return Pattern(self.minterms | other.minterms)

    def __and__(self, other):
        rv = Pattern()
        for left_mt in self.minterms:
            rv.minterms |= set(left_mt | right_mt for right_mt in other.minterms)
        return rv

    def __str__(self):
        return ' | '.join([' & '.join(map(str, mt)) for mt in self.minterms])

    def __repr__(self):
        return 'Pattern<%r>' % (' | '.join([' & '.join(map(repr, mt)) for mt in self.minterms]))


def make_minterm(*symbols):
    if len(symbols) > 0:
        return set([frozenset([sym for sym in symbols])])
    else:
        return set()


def make_pattern(*symbols):
    return Pattern(make_minterm(*symbols))
