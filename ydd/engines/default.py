# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

from functools import wraps
from weakref import WeakValueDictionary

from .abc import AbstractEngine, AbstractRoot


class Root(AbstractRoot):

    def __init__(self, key=None, then_=None, else_=None, creator=None):
        self._key = key
        self._then = then_
        self._else = else_

        self.creator = creator

    @property
    def key(self):
        return self._key

    @property
    def then_(self):
        return self._then

    @property
    def else_(self):
        return self._else

    def is_zero(self):
        return False

    def is_one(self):
        return False

    def __len__(self):
        return self.creator.len(self)

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

    def __or__(self, other):
        return self.creator.union(self, other)

    def __and__(self, other):
        return self.creator.intersection(self, other)

    def __sub__(self, other):
        return self.creator.difference(self, other)

    def __xor__(self, other):
        return self.creator.symmetric_difference(self, other)

    def __hash__(self):
        return hash((self.key, id(self.then_), id(self.else_)))


class OneTerminal(Root):

    def is_one(self):
        return True

    def __lt__(self, other):
        if other.is_zero() or other.is_one():
            return False
        return self < other.else_

    def __le__(self, other):
        if other.is_zero() or other.is_one():
            return self is other
        return self <= other.else_

    def __ge__(self, other):
        return self is other

    def __gt__(self, other):
        return other is self.creator.zero


class ZeroTerminal(Root):

    def is_zero(self):
        return True

    def __contains__(self, el):
        return False

    def __lt__(self, other):
        return self is not other

    def __le__(self, other):
        return True

    def __ge__(self, other):
        return self is other

    def __gt__(self, other):
        return False


class DefaultEngine(AbstractEngine):

    def __init__(self, use_weak_table=False):
        self.zero = ZeroTerminal(key=False, creator=self)
        self.one = OneTerminal(key=True, creator=self)

        self._table = {
            self._hash_node(self.zero): self.zero,
            self._hash_node(self.one): self.one
        }

        if use_weak_table:
            self._table = WeakValueDictionary(self._table)

        self._cache = {
            'len': {},
            'union': {},
            'intersection': {},
            'difference': {},
            'symmetric_difference': {}
        }

    def cached(keygen=None):
        def decorate(fn):
            @wraps(fn)
            def decorated(self, *args):
                cache = self._cache[fn.__name__]
                if keygen is None:
                    cache_key = tuple([id(arg) for arg in args])
                else:
                    cache_key = tuple(keygen(*args))
                try:
                    return cache[cache_key]
                except KeyError:
                    rv = fn(self, *args)
                cache[cache_key] = fn(self, *args)
                return rv
            return decorated
        return decorate

    def make_terminal(self, terminal):
        if terminal:
            return self.one
        else:
            return self.zero

    def make_node(self, key, then_, else_):
        # Apply the ZDD-reduction rule at the node creation, so we make sure
        # to create canonical forms only.
        if then_ is self.zero:
            return else_

        # Create a temporary node.
        rv = Root(key=key, then_=then_, else_=else_, creator=self)

        # Try to return the node from the unique table.
        h = self._hash_node(rv)
        try:
            return self._table[h]
        except KeyError:
            self._table[h] = rv
            return rv

    @cached(keygen=lambda l, r: [l, r] if (id(l) < id(r)) else [r, l])
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
            return self.make_node(
                key=left.key,
                then_=left.then_,
                else_=self.union(left.else_, right)
            )

        if right.key == left.key:
            # If the left operand start with the same key as the right one,
            # then we should continue on the both their children.
            return self.make_node(
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
            return self.make_node(
                key=right.key,
                then_=right.then_,
                else_=self.union(left, right.else_)
            )

    @cached(keygen=lambda l, r: [l, r] if (id(l) < id(r)) else [r, l])
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
            return self.make_node(
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

    @cached()
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
            return self.make_node(
                key=left.key,
                then_=left.then_,
                else_=self.difference(left.else_, right)
            )

        if right.key == left.key:
            # If the left operand start with the same key as the right one,
            # then we should continue on the both their children.
            return self.make_node(
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

    @cached(keygen=lambda l, r: [l, r] if (id(l) < id(r)) else [r, l])
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
            # If the left operand is the one terminal, then we can keep all
            # paths from the right one, except its "else-most" terminal that
            # should be zero, in order to exclude the left operand.
            return self._update_else_most_terminal(right, self.zero)

        if right.key > left.key:
            # If the right operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the left's starting key
            # appears. As a result, we can continue only on the "else" child
            # of the left operand only.
            return self.make_node(
                key=left.key,
                then_=left.then_,
                else_=self.symmetric_difference(left.else_, right)
            )

        if right.key == left.key:
            # If the left operand start with the same key as the right one,
            # then we should continue on the both their children.
            return self.make_node(
                key=left.key,
                then_=self.symmetric_difference(left.then_, right.then_),
                else_=self.symmetric_difference(left.else_, right.else_)
            )

        if right.key < left.key:
            # If the left operand starts with a greater key, it implies that
            # it doesn't have an accepting path where the right's starting key
            # appears. As a result, we can keep then "then" child of the right
            # operand unchanged, and continue on its "else" child.
            return self.make_node(
                key=right.key,
                then_=right.then_,
                else_=self.difference(left, right.else_)
            )
            return self.difference(left, right.else_)

    @cached()
    def len(self, ydd):
        if ydd is self.zero:
            return 0
        if ydd is self.one:
            return 1
        return self.len(ydd.else_) + self.len(ydd.then_)

    def _hash_node(self, node):
        return (node.key, id(node.then_), id(node.else_))

    def _update_else_most_terminal(self, ydd, child):
        if ydd in (self.one, self.zero):
            return child
        elif ydd.else_ in (self.one, self.zero):
            return self.make_node(key=ydd.key, then_=ydd.then_, else_=child)
        else:
            return self._update_else_most_terminal(ydd.else_, child)
