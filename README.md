#py-ydd
A library to use YaDDs with Python.

## Installation
Simply type `python setup.py install` to install py-ydd.

## Usage
```
from ydd.ydd import Engine

engine = Engine()
family = engine.make({1,2,3}, {1,2})
print(family.enum())
>>> [{1, 2, 3}, {1, 2}]

family = family | engine.make_one({4,5})
print(family.enum())
>>> [{1, 2, 3}, {1, 2}, {4,5}]
```

## Tests
To run the tests, type `python -m unittest discover`.
