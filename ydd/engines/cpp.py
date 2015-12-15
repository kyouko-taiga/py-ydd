# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

from ._cpp import *
from .abc import AbstractEngine, AbstractRoot


IntEngine.__bases__ += (AbstractEngine,)
IntRoot.__bases__ += (AbstractRoot,)

PNEngine.__bases__ += (AbstractEngine,)
PNRoot.__bases__ += (AbstractRoot,)


def pn_place_str(self):
    return '%s:%i' % (self.id_, self.tokens)

PNPlace.__str__ = pn_place_str


def pn_place_repr(self):
    return 'Place<%s:%i>' % (self.id_, self.tokens)

PNPlace.__repr__ = pn_place_repr
