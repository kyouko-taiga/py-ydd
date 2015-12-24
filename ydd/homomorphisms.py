# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.


class Homomorphism(object):

    def __init__(self, engine):
        self.engine = engine


class Identity(Homomorphism):

    def __call__(self, ydd):
        return ydd


class Reject(Homomorphism):

    def __call__(self, ydd):
        return self.engine.make_terminal(False)


class Accept(Homomorphism):

    def __call__(self, ydd):
        return self.engine.make_terminal(True)


class Union(Homomorphism):

    def __init__(self, engine, left, right):
        super().__init__(engine)
        self.left = left
        self.right = right

    def __call__(self, ydd):
        return self.left(ydd) | self.right(ydd)


class Intersection(Homomorphism):

    def __init__(self, engine, left, right):
        super().__init__(engine)
        self.left = left
        self.right = right

    def __call__(self, ydd):
        return self.left(ydd) & self.right(ydd)


class Difference(Homomorphism):

    def __init__(self, engine, left, right):
        super().__init__(engine)
        self.left = left
        self.right = right

    def __call__(self, ydd):
        return self.left(ydd) - self.right(ydd)


class SymmetricDifference(Homomorphism):

    def __init__(self, engine, left, right):
        super().__init__(engine)
        self.left = left
        self.right = right

    def __call__(self, ydd):
        return self.left(ydd) ^ self.right(ydd)


class Update(Homomorphism):

    def __init__(self, engine, pattern):
        super().__init__(engine)

        if len(pattern.minterms) > 1:
            raise ValueError('Cannot update a set with a disjunctive pattern.')
        self.symbols = sorted(next(iter(pattern.minterms)))

    def __call__(self, ydd):
        if ydd.is_zero():
            return ydd

        for sym in self.symbols:
            if sym.enabled:
                ydd = self._set(sym.value, ydd)
            else:
                ydd = self._unset(sym.value, ydd)

        return ydd

    def _set(self, key, ydd):
        if ydd.is_zero():
            return ydd

        if ydd.is_one() or (ydd.key > key):
            return self.engine.make_node(key, ydd, self.engine.make_terminal(False))

        if ydd.key == key:
            return self.engine.make_node(
                ydd.key,
                ydd.then_ | ydd.else_,
                self.engine.make_terminal(False))

        if ydd.key < key:
            return self.engine.make_node(
                ydd.key,
                self._set(key, ydd.then_),
                self._set(key, ydd.else_))

    def _unset(self, key, ydd):
        if ydd.is_zero():
            return ydd

        if ydd.is_one() or (ydd.key > key):
            return ydd

        if ydd.key == key:
            return ydd.then_ | ydd.else_

        if ydd.key < key:
            return self.engine.make_node(
                ydd.key,
                self._unset(key, ydd.then_),
                self._unset(key, ydd.else_))


class Filter(Homomorphism):

    def __init__(self, engine, pattern, homomorphism):
        super().__init__(engine)
        self.pattern = pattern
        self.homomorphism = homomorphism

    def __call__(self, ydd):
        # Sort the keys in each minterm of the pattern.
        sorted_minterms = (sorted(mt) for mt in self.pattern.minterms)

        satisfied = self.engine.make_terminal(False)

        # Filter the DDs that satisfiy the given minterms.
        for smt in sorted_minterms:
            satisfied = satisfied | self._filter(ydd, smt)

        return self.homomorphism(satisfied)

    def _filter(self, ydd, minterm):
        if ydd.is_zero() or (len(minterm) == 0):
            return ydd

        zero = self.engine.make_terminal(False)
        sym = minterm[0]

        if sym.enabled:
            if ydd.is_one() or (ydd.key > sym.value):
                return zero
            if ydd.key == sym.value:
                return self.engine.make_node(
                    ydd.key,
                    self._filter(ydd.then_, minterm[1:]),
                    zero)

        else:
            if ydd.is_one() or (ydd.key > sym.value):
                return self._filter(ydd, minterm[1:])
            if ydd.key == sym.value:
                return self._filter(ydd.else_, minterm[1:])

        # ydd.key < sym.value
        return self.engine.make_node(
            ydd.key,
            self._filter(ydd.then_, minterm),
            self._filter(ydd.else_, minterm))
