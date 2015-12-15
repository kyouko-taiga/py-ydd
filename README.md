#py-ydd
py-ydd is a library to use YDDs (Yet another Decision Diagrams) with Python.
Such structure allows to efficiently store extremely large families of sets, and perform various operations on them quiet efficiently.

## Usage
### Families of sets
A YDD is an acyclic graph where each node represents a different family of set.
To make sure those nodes are unique in the entire graph, py-ydd relies on *engines* to handle the construction of new YDDs.

Go on an create your engine:

```python
from ydd.engines.default import DefaultEngine as Engine
engine = Engine()
```

The `DefaultEngine` is pure Python class.
It can't compete in terms of performances with the ones that are written in C++, but it is handy to quickly test something, or prototype your code.

Now you're ready to create your families of sets:

```python
family = engine.make({1, 2, 3}, {1, 2})
print(list(family))
>>> [frozenset({1, 2}), frozenset({1, 2, 3})]
```

And you can perform various kind of operations on them.
Note that families of sets behave like Python's [built-in sets](https://docs.python.org/3/library/stdtypes.html?highlight=set#set), and implement the same operations.

```python
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

### Homomorphisms
Basic operations such as the union, the intersection, etc. may be nice, but you'll certainly want to create your own homomorphisms.
In order to do that, you can use the two lower-level methods all engines implement: `make_terminal` and `make_node`.

To understand how to use those methods, one has to understand how a YDD encodes its elements first.
Each element (i.e. each encoded set), is represented as a collection of keys (i.e. elements of the set).
Each node of the graph represents a key, and has two children (`then`, and `else`) that represent other keys, the rejecting terminal or the accepting terminal.
A path from the root to the accepting terminal represents a set.
On this path, choosing the `then` child of a node indicates that its key is a member of the set, while choosing its `else` child indicates it isn't.
Any path that leads to the rejecting terminal isn't a member of the family.

For example, take the family `[{1, 2}, {1}]`, represented by the following YDD:

```
1 -> (
  then: 2 -> (
    then: $1,
    else: $1
  ),
  else: $0
)
```

_Note that you can obtain a similar output if you type `repr(engine.make({1, 2}, {1}))`._

Now let's go back to our methods.

`make_terminal(terminal: bool) -> Root` allows you to create terminal nodes.
The parameter `terminal` tells the engine to create either the accepting terminal (`True`) or the rejecting one (`False`).

`make_node(key: object, then_: Root, else_: Root) -> Root` allows you to create any kind of node.
The `DefaultEngine` can accept any type for the `key`, as long as it is hashable and comparable to the other keys of the YDD.
Be careful when using this method to make sure that the keys of `then_` and `else_` are strictly greater than `key`, otherwise you'll break the nodes canonicity.

Alright! Enoug theory, let's see an example.
Here's a homomorphism that returns all sets containing the element `42`:

```python
def sets_containing_42(engine, family):
    if family.is_zero() or family.is_one():
        return engine.make_terminal(False)

    if family.key < 42:
        return engine.make_node(
            family.key,
            sets_containing_42(engine, family.then_),
            sets_containing_42(engine, family.else_))
    elif family.key == 42:
        return engine.make_node(
            family.key,
            family.then_,
            engine.make_terminal(False))
    elif family.key > 42:
        return engine.make_terminal(False)
```

If the given family node is terminal, obviously it can't contain `42`, so we simply return the rejecting terminal (representing the empty family).
Then if the node's key is smaller than `42`, we return a new node with the same key, but we create its children by applying the homomorphism to those of the original node.
Finally, if the node's key is greater, we return the rejecting terminal since we know `42` can't be contained in any path starting from there.

## Installation
### Requirements
For performance reasons, the core of py-ydd is implemented in C++, and uses [Boost.Python](http://www.boost.org/doc/libs/1_59_0/libs/python/) to interface it with Python.
Thus, you need to install [Boost](http://www.boost.org) (or at least Boost.Python) first.

_You can skip the remaining of this chapter if you already have Boost.Python installed on your system._

[Download](http://www.boost.org/users/download/) the latest version of Boost (1.59.0 as of this writing), decompress the archive and navigate to its directory.
There, type

```bash
./bootstrap.sh --with-libraries=python
```

If you're Python executable is not located at a unusual location, pass the parameter `--with-python=/path/to/python` to the above command.
Boost usually detects automatically the correct paths for the includes and libraries directories, but might fail to do so on some systems (for instance if you have Python installed with macports on OS X), which would be the cause of the dreaded `pyconfig.h: No such file or directory`.
To address this issue, edit the file `projet-config.jam` and replace

```
if ! [ python.configured ]
{
    using python : 3.5 : /path/to/python ;
}
```

with

```
if ! [ python.configured ]
{
    using python
      : 3.x
      : /path/to/python
      : /path/to/includes
      : /path/to/libraries
      ;
}
```

Now you're ready to run Boost's build tool:

```bash
./b2 install
```

It'll install Boost.Python to your `/usr/local/`.

Please refer to the [official documentation](http://www.boost.org/doc/libs/1_59_0/more/getting_started/index.html) of Boost for troubleshooting, or if you're running Windows.

### Installation of py-ydd
Once the requirements installed, you can simply type

```
python setup.py install
```

to install py-ydd on your system.

## Tests
To run the tests, type `python -m unittest discover`.
