# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

import sys


_maxsize = sys.maxsize


def hash_int(i):
    return (i % _maxsize) * 2654435761


def hash_key(key):
    if isinstance(key, int):
        return hash_int(key)
    return hash(key)


def hash_node(key, then_, else_):
    return hash((hash_key(key), id(then_), id(else_)))
