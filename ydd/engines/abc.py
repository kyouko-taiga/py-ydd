# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

from abc import ABCMeta, abstractmethod, abstractproperty
from collections.abc import Hashable


class AbstractRoot(Hashable, metaclass=ABCMeta):

    @abstractproperty
    def key(self):
        pass

    @abstractproperty
    def then_(self):
        pass

    @abstractproperty
    def else_(self):
        pass

    @abstractmethod
    def is_zero(self):
        pass

    @abstractmethod
    def is_one(self):
        pass

    def _hash(self):
        # See the notes on hashability using collections.abc.Set.
        return hash(self)

    def __iter__(self):

        # Implementation note: The iteration process sees the DD as a tree,
        # and explores all his nodes with a in-order traversal. During this
        # traversal, we store all the of the "then" parents, so that we can
        # produce a item whenever we reach the one terminal.

        rv = []
        stack = []
        node = self

        while not node.is_zero():
            if node.is_one():
                yield frozenset(rv)
                try:
                    node = stack.pop()
                except IndexError:
                    return
                rv = list(filter(lambda e: e < node.key, rv)) + [node.key]
                node = node.then_
            elif not node.else_.is_zero():
                stack.append(node)
                node = node.else_
            else:
                rv.append(node.key)
                node = node.then_

    def __ge__(self, other):
        return (other <= self)

    def __gt__(self, other):
        return (other < self)

    def __str__(self):
        return str([set(s) for s in self])

    def __repr__(self):
        if self.is_zero():
            return '$0'
        elif self.is_one():
            return '$1'
        else:
            return '%r -> (then: %r, else: %r)' % (self.key, self.then_, self.else_)
