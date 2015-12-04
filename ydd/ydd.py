# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

from functools import reduce
from operator import or_
from weakref import WeakValueDictionary

from ydd.utils import hash_node


class YDD(object):

    def __init__(self, key=None, then_=None, else_=None, creator=None):
        self.key = key
        self.then_ = then_
        self.else_ = else_

        self.creator = creator

    def __or__(self, other):
        return self.creator.union(self, other)

    def __and__(self, other):
        return self.creator.intersection(self, other)

    def enum(self):
        if self.then_ is self.creator.zero:
            then_rv = set()
        else:
            then_rv = [set((self.key,)) | tail for tail in self.then_.enum()]

        if self.else_ is self.creator.zero:
            else_rv = []
        else:
            else_rv = self.else_.enum()

        return then_rv + else_rv

    def pprint(self, indent=4, level=1):
        indentation = (' ' * indent * level)

        rv = str(self.key) + ' -> (\n'
        rv += indentation + 'then: ' + self.then_.pprint(indent=indent, level=level + 1)
        rv += indentation + 'else: ' + self.else_.pprint(indent=indent, level=level + 1)
        rv += (' ' * indent * (level - 1)) + ')\n'

        if (level == 1):
            rv = rv.strip('\n')
        return rv

    def __hash__(self):
        return hash_node(self.key, self.then_, self.else_)

    def __str__(self):
        return str(self.enum())

    def __repr__(self):
        return '%r -> (then: %r, else: %r)' % (self.key, self.then_, self.else_)


class Terminal(YDD):

    def enum(self):
        return [set()]

    def pprint(self, indent=2, level=1):
        return self.key + '\n'

    def __str__(self):
        return self.key

    def __repr__(self):
        return self.key


class Engine(object):

    def __init__(self, use_weak_table=False):
        self.one = Terminal(key='$1', creator=self)
        self.zero = Terminal(key='$0', creator=self)

        self._table = {
            hash(self.one): self.one,
            hash(self.zero): self.zero
        }

        if use_weak_table:
            self._table = WeakValueDictionary(self._table)

        self._memoization = {}

    def make(self, *iterables):
        # If there aren't any iterables, return a DD encoding the empty set.
        if len(iterables) == 0:
            return self.zero

        # Generate a DD for all given iterables, and make their union.
        return reduce(or_, (self.make_one(it) for it in iterables))

    def make_one(self, iterable):
        # If there aren't any elements, return a DD encoding the empty set.
        if len(iterable) == 0:
            return self.one

        # Make sure the elements are unique, and sort them greatest first.
        elements = sorted(set(iterable), reverse=True)

        # Create the new DD.
        rv = self.one
        for i, el in enumerate(elements):
            rv = self._make_node(key=el, then_=rv, else_=self.zero)

        return rv

    def _make_node(self, key, then_, else_):
        # Apply the ZDD-reduction rule at the node creation, so we make sure
        # to create canonical forms only.
        if then_ is self.zero:
            return else_

        # Try to return the node from the cache if it's already been built.
        # Note that if is faster to try accessing the table and catch KeyError
        # KeyError exceptions if we expect the table to grow big enough to be
        # likely to already contain the desired nodes.
        h = hash_node(key, then_, else_)
        try:
            return self._table[h]
        except KeyError:
            # Since the unique table doesn't keep the objects that aren't
            # otherwise referenced, we are forced to assign the built DD to a
            # temporary variable before we insert it in the unique table.
            rv = YDD(key=key, then_=then_, else_=else_, creator=self)
            self._table[h] = rv
            return rv

    def union(self, left, right):
        if right is self.one:
            # If the right operand is the one terminal, then we return the
            # left operand, making sure its "else-most" terminal is also one.
            return self._update_else_most_terminal(left, self.one)

        if right is self.zero:
            # If the right operand is the zero terminal, then we simply return
            # the left operand unchanged, as no new path should be merged.
            return left

        if left is self.one:
            # If the left operand is the one terminal, then we return the
            # right operand, making sure its "else-most" terminal is also one.
            return self._update_else_most_terminal(right, self.one)

        if left is self.zero:
            # If the left operand is the zero terminal, then we simply return
            # the right operand unchanged.
            return right

        if right.key > left.key:
            # If the right operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the left's starting key
            # appears. As a result, we should continue the union only on the
            # "else" child of the left operand.
            return self._make_node(
                key=left.key,
                then_=left.then_,
                else_=self.union(left.else_, right)
            )

        if right.key == left.key:
            # If the left operand start with the same key as the right one,
            # then we should continue the union on the both their children.
            return self._make_node(
                key=left.key,
                then_=self.union(left.then_, right.then_),
                else_=self.union(left.else_, right.else_)
            )

        if right.key < left.key:
            # If the left operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the right's starting key
            # appears. As a result, we should return a new node that puts the
            # the "then" child of the right operand on its own "then" child,
            # and continue the union on its "else" child.
            return self._make_node(
                key=right.key,
                then_=right.then_,
                else_=self.union(left, right.else_)
            )

    def intersection(self, left, right):
        if (right is self.zero) or (left is self.zero):
            # If either the left or right operand is the zero terminal, then
            # we can discard all the paths from the other operand.
            return self.zero

        if (right is self.one):
            # If the right operand is the one terminal, then we can discard
            # all paths from the left one, except its "else-most" as it
            # corresponds to the absence of all remaining keys.
            node = left
            while node not in (self.one, self.zero):
                node = node.else_
            return node

        if (left is self.one):
            # If the left operand is the one terminal, then we can discard
            # all paths from the right one, except its "else-most" as it
            # corresponds to the absence of all remaining keys.
            node = right
            while node not in (self.one, self.zero):
                node = node.else_
            return node

        if right.key > left.key:
            # If the right operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the left's starting key
            # appears. As a result, we can discard the "then" child of the
            # left operand and continue the intersection on its "else" child.
            return self.intersection(left.else_, right)

        if right.key == left.key:
            # If the left operand start with the same key as the right one,
            # then we should continue the union on the both their children.
            return self._make_node(
                key=left.key,
                then_=self.intersection(left.then_, right.then_),
                else_=self.intersection(left.else_, right.else_)
            )

        if right.key < left.key:
            # If the left operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the right's starting key
            # appears. As a result, we can discard the "then" child of the
            # right operand and continue the intersection on its "else" child.
            return self.intersection(left, right.else_)

    def _update_else_most_terminal(self, ydd, child):
        if ydd in (self.one, self.zero):
            return child
        elif ydd.else_ in (self.one, self.zero):
            return self._make_node(key=ydd.key, then_=ydd.then_, else_=child)
        else:
            return self._update_else_most_terminal(ydd.else_, child)
