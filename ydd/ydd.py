# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

from collections.abc import Set, Hashable
from functools import reduce, wraps
from operator import or_
from weakref import WeakValueDictionary

from ydd.utils import hash_node


class YDD(Set, Hashable):

    def __init__(self, key=None, then_=None, else_=None, creator=None):
        self.key = key
        self.then_ = then_
        self.else_ = else_

        self.creator = creator

    def __contains__(self, item):

        # Implementation note: We try to find a path that ends on the one
        # terminal for which there's a node for every element of the given
        # item whose "then" child is not the zero terminal.

        elements = sorted(item, reverse=True)
        node = self

        while (node not in (self.creator.one, self.creator.zero)) and elements:
            el = elements[-1]
            if el > node.key:
                node = node.else_
            elif el == node.key:
                node = node.then_
                elements.pop()
            else:
                node = node.else_
                elements.pop()

        return (not bool(elements)) and (node is self.creator.one)

    def __iter__(self):

        # Implementation note: The iteration process sees the DD as a tree,
        # and explores all his nodes with a in-order traversal. During this
        # traversal, we store all the of the "then" parents, so that we can
        # produce a item whenever we reach the one terminal.

        rv = []
        stack = []
        node = self

        while node is not self.creator.zero:
            if node is self.creator.one:
                yield frozenset(rv)
                try:
                    node = stack.pop()
                except IndexError:
                    return
                rv = list(filter(lambda e: e < node.key, rv)) + [node.key]
                node = node.then_
            elif node.else_ is not self.creator.zero:
                stack.append(node)
                node = node.else_
            else:
                rv.append(node.key)
                node = node.then_

    def __len__(self):
        return len(self.else_) + len(self.then_)

    def __lt__(self, other):
        if other in (self.creator.one, self.creator.zero):
            # We can assume that self is not a terminal node, since __lt__ is
            # overridden in the terminal classes. Thus it has a "then" and
            # child, implying it can't be contained within a terminal.
            return False

        if other.key > self.key:
            return False
        if other.key == self.key:
            return (
                (self is not other) and
                ((self.then_ <= other.then_) and (self.else_ <= other.else_))
            )
        if other.key < self.key:
            return self < other.else_

    def __le__(self, other):
        if other in (self.creator.one, self.creator.zero):
            # We can assume that self is not a terminal node, since __le__ is
            # overridden in the terminal classes. Thus it has a "then" and
            # child, implying it can't be contained within a terminal.
            return False

        if other.key > self.key:
            return False
        if other.key == self.key:
            return (self is other) or ((self.then_ <= other.then_) and (self.else_ <= other.else_))
        if other.key < self.key:
            return self <= other.else_

    def __eq__(self, other):
        return self is other

    def __ge__(self, other):
        return not (other < self)

    def __gt__(self, other):
        return not (other < self)

    def __or__(self, other):
        return self.creator.union(self, other)

    def __and__(self, other):
        return self.creator.intersection(self, other)

    def __sub__(self, other):
        return self.creator.difference(self, other)

    def __xor__(self, other):
        return self.creator.symmetric_difference(self, other)

    def isdisjoint(self, other):
        return (self & other) is self.creator.zero

    def pprint(self, indent=4, level=1):
        indentation = (' ' * indent * level)

        rv = str(self.key) + ' -> (\n'
        rv += indentation + 'then: ' + self.then_.pprint(indent=indent, level=level + 1)
        rv += indentation + 'else: ' + self.else_.pprint(indent=indent, level=level + 1)
        rv += (' ' * indent * (level - 1)) + ')\n'

        if (level == 1):
            rv = rv.strip('\n')
        return rv

    def _hash(self):
        # See the notes on hashability using collections.abc.Set.
        return hash(self)

    def __hash__(self):
        return hash_node(self.key, self.then_, self.else_)

    def __str__(self):
        return str(list(self))

    def __repr__(self):
        return '%r -> (then: %r, else: %r)' % (self.key, self.then_, self.else_)


class Terminal(YDD):

    def pprint(self, indent=2, level=1):
        return self.key + '\n'

    def __str__(self):
        return self.key

    def __repr__(self):
        return self.key


class OneTerminal(Terminal):

    def __len__(self):
        return 1

    def __lt__(self, other):
        if other in (self, self.creator.zero):
            return False
        return self < other.else_

    def __le__(self, other):
        if other in (self, self.creator.zero):
            return self is other
        return self <= other.else_

    def __ge__(self, other):
        return self is other

    def __gt__(self, other):
        return other is self.creator.zero


class ZeroTerminal(Terminal):

    def __contains__(self, el):
        return False

    def __len__(self):
        return 0

    def __lt__(self, other):
        return self is not other

    def __le__(self, other):
        return True

    def __ge__(self, other):
        return self is other

    def __gt__(self, other):
        return False


class Engine(object):

    def __init__(self, use_weak_table=False):
        self.one = OneTerminal(key='$1', creator=self)
        self.zero = ZeroTerminal(key='$0', creator=self)

        self._table = {
            hash(self.one): self.one,
            hash(self.zero): self.zero
        }

        if use_weak_table:
            self._table = WeakValueDictionary(self._table)

        self._cache = {}

    def cached(fn):
        @wraps(fn)
        def decorated(self, *args):
            cache_key = hash(tuple([fn.__name__] + list(args)))
            try:
                return self._cache[cache_key]
            except KeyError:
                self._cache[cache_key] = fn(self, *args)
            return self._cache[cache_key]
        return decorated

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

    @cached
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
            # appears. As a result, we should continue only on the "else"
            # child of the left operand.
            return self._make_node(
                key=left.key,
                then_=left.then_,
                else_=self.union(left.else_, right)
            )

        if right.key == left.key:
            # If the left operand start with the same key as the right one,
            # then we should continue on the both their children.
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
            # and continue on its "else" child.
            return self._make_node(
                key=right.key,
                then_=right.then_,
                else_=self.union(left, right.else_)
            )

    @cached
    def intersection(self, left, right):
        if (right is self.zero) or (left is self.zero):
            # If either the left or right operand is the zero terminal, then
            # we can discard all the paths from the other operand.
            return self.zero

        if right is self.one:
            # If the right operand is the one terminal, then we can discard
            # all paths from the left one, except its "else-most" terminal,
            # as it corresponds to the absence of all remaining keys.
            node = left
            while node not in (self.one, self.zero):
                node = node.else_
            return node

        if left is self.one:
            # If the left operand is the one terminal, then we can discard
            # all paths from the right one, except its "else-most" terminal,
            # as it corresponds to the absence of all remaining keys.
            node = right
            while node not in (self.one, self.zero):
                node = node.else_
            return node

        if right.key > left.key:
            # If the right operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the left's starting key
            # appears. As a result, we can discard the "then" child of the
            # left operand and continue on its "else" child.
            return self.intersection(left.else_, right)

        if right.key == left.key:
            # If the left operand start with the same key as the right one,
            # then we should continue on the both their children.
            return self._make_node(
                key=left.key,
                then_=self.intersection(left.then_, right.then_),
                else_=self.intersection(left.else_, right.else_)
            )

        if right.key < left.key:
            # If the left operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the right's starting key
            # appears. As a result, we can discard the "then" child of the
            # right operand and continue on its "else" child.
            return self.intersection(left, right.else_)

    @cached
    def difference(self, left, right):
        if right is self.zero:
            # If the right operand is the zero terminal, then we simply return
            # the left operand unchanged.
            return left

        if right is self.one:
            # If the right operand is the one terminal, then we can keep all
            # paths from the left one, except its "else-most" terminal that
            # should be zero, in order to exclude the right operand.
            return self._update_else_most_terminal(left, self.zero)

        if left is self.zero:
            # If the left operand is the zero terminal, we simply return it.
            return left

        if left is self.one:
            # If the left operand is the one terminal, then we return it as-is
            # only if the "else-most" terminal of the right operand is zero.
            node = right
            while node not in (self.one, self.zero):
                node = node.else_
            return self.one if node is self.zero else self.zero

        if right.key > left.key:
            # If the right operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the left's starting key
            # appears. As a result, we can continue only on the "else" child
            # of the left operand only.
            return self._make_node(
                key=left.key,
                then_=left.then_,
                else_=self.difference(left.else_, right)
            )

        if right.key == left.key:
            # If the left operand start with the same key as the right one,
            # then we should continue on the both their children.
            return self._make_node(
                key=left.key,
                then_=self.difference(left.then_, right.then_),
                else_=self.difference(left.else_, right.else_)
            )

        if right.key < left.key:
            # If the left operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the right's starting key
            # appears. As a result, we don't care about any path on the "then"
            # child of the right operand and can continue on its "else" child.
            return self.difference(left, right.else_)

    @cached
    def symmetric_difference(self, left, right):
        if right is self.zero:
            # If the right operand is the zero terminal, then we simply return
            # the left operand unchanged.
            return left

        if right is self.one:
            # If the right operand is the one terminal, then we can keep all
            # paths from the left one, except its "else-most" terminal that
            # should be zero, in order to exclude the right operand.
            return self._update_else_most_terminal(left, self.zero)

        if left is self.zero:
            # If the left operand is the zero terminal, then we simply return
            # the right operand unchanged.
            return right

        if left is self.one:
            # If the left operand is the one terminal, then we return it as-is
            # only if the "else-most" terminal of the right operand is zero.
            node = right
            while node not in (self.one, self.zero):
                node = node.else_
            return self.one if node is self.zero else self.zero

        if right.key > left.key:
            # If the right operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the left's starting key
            # appears. As a result, we can continue only on the "else" child
            # of the left operand only.
            return self._make_node(
                key=left.key,
                then_=left.then_,
                else_=self.symmetric_difference(left.else_, right)
            )

        if right.key == left.key:
            # If the left operand start with the same key as the right one,
            # then we should continue on the both their children.
            return self._make_node(
                key=left.key,
                then_=self.symmetric_difference(left.then_, right.then_),
                else_=self.symmetric_difference(left.else_, right.else_)
            )

        if right.key < left.key:
            # If the left operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the right's starting key
            # appears. As a result, we can keep then "then" child of the right
            # operand unchanged, and continue on its "else" child.
            return self._make_node(
                key=right.key,
                then_=right.then_,
                else_=self.difference(left, right.else_)
            )
            return self.difference(left, right.else_)

    def _update_else_most_terminal(self, ydd, child):
        if ydd in (self.one, self.zero):
            return child
        elif ydd.else_ in (self.one, self.zero):
            return self._make_node(key=ydd.key, then_=ydd.then_, else_=child)
        else:
            return self._update_else_most_terminal(ydd.else_, child)
