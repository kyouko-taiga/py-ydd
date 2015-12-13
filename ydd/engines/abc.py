# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

from abc import ABCMeta, abstractmethod, abstractproperty
from collections.abc import Hashable
from functools import reduce
from operator import or_


class AbstractEngine(metaclass=ABCMeta):

    @abstractmethod
    def make_terminal(self, terminal):
        pass

    @abstractmethod
    def make_node(self, key, then_, else_):
        pass

    def make(self, *containers):
        if len(containers) == 0:
            return self.make_terminal(False)
        return reduce(or_, (self.make_from_container(it) for it in containers))

    def make_from_container(self, container):
        if len(container) == 0:
            return self.make_terminal(True)

        # Remove duplicates and sort the container.
        elements = sorted(set(container), reverse=True)

        # Create the DD.
        rv = self.make_terminal(True)
        zero = self.make_terminal(False)
        for i, el in enumerate(elements):
            rv = self.make_node(el, rv, zero)
        return rv


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

    def isdisjoint(self, other):
        return (self & other).is_zero()

    def _hash(self):
        # See the notes on hashability using collections.abc.Set.
        return hash(self)

    def __contains__(self, item):

        # Implementation note: We try to find a path that ends on the one
        # terminal for which there's a node for every element of the given
        # item whose "then" child is not the zero terminal.

        node = self

        if len(item) == 0:
            while not (node.is_zero() or node.is_one()):
                node = node.else_
            return node.is_one()

        elements = sorted(item, reverse=True)

        while (not (node.is_zero() or node.is_one())) and elements:
            el = elements[-1]
            if el > node.key:
                node = node.else_
            elif el == node.key:
                node = node.then_
                elements.pop()
            else:
                node = node.else_
                elements.pop()

        while not (node.is_zero() or node.is_one()):
            node = node.else_

        return (not bool(elements)) and node.is_one()

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
