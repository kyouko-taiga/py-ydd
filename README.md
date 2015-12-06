#py-ydd
A library to use YaDDs with Python.

## Installation
Simply type `python setup.py install` to install py-ydd.

## Usage
First, you need to create an *engine* to handle the construction of new YaDDs, as well as the operations that'll be performed on them.

```
from ydd.ydd import Engine
engine = Engine()
```

By default, an engine will keep a reference to all created YaDDs, even if those that aren't referenced anymore, which may lead to huge wastes of memory in some cases.
You can change with the flag `use_weak_table`, but keep in mind that this option might impact the performances.

```
engine = Engine(use_weak_table=True)
```

Now you're ready to create your families of sets:

```
family = engine.make({1, 2, 3}, {1, 2})
print(list(family))
>>> [frozenset({1, 2}), frozenset({1, 2, 3})]
```

And to perform any kind of operations on them:

```
family = family | engine.make({4 ,5})
print(list(family))
>>> [frozenset({4, 5}), frozenset({1, 2}), frozenset({1, 2, 3})]

family = family & engine.make({4, 5}, {1, 2, 3}, {6, 7})
print(list(family))
>>> [frozenset({4, 5}), frozenset({1, 2, 3})]

family = family - engine.make({1, 2, 3})
print(list(family))
>>> [frozenset({4, 5})]
```

## Tests
To run the tests, type `python -m unittest discover`.
