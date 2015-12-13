from ._cpp import *
from .abc import AbstractRoot


IntRoot.__bases__ += (AbstractRoot,)
