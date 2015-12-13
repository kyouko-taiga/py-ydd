# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

from ._cpp import *
from .abc import AbstractEngine, AbstractRoot


IntEngine.__bases__ += (AbstractEngine,)
IntRoot.__bases__ += (AbstractRoot,)
