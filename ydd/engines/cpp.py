from ._cpp import *
from .abc import AbstractEngine, AbstractRoot

IntEngine.__bases__ += (AbstractEngine,)
IntRoot.__bases__ += (AbstractRoot,)
