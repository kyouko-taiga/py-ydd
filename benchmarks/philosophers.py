import argparse
import time

from functools import wraps

from ydd.ydd import Engine


class Place(object):

    def __init__(self, name, tokens=0):
        self.name = name
        self.tokens = tokens

    def __lt__(self, other):
        if self.name == other.name:
            return self.tokens < other.tokens
        else:
            return self.name < other.name

    def __eq__(self, other):
        return (self.name == other.name) and (self.tokens == other.tokens)

    def __hash__(self):
        return hash((self.name, self.tokens))

    def __str__(self):
        return '%s:%i' % (self.name, self.tokens)

    def __repr__(self):
        return 'Place<%s:%i>' % (self.name, self.tokens)


class PetriNet(object):

    def __init__(self, engine, pre, post, m0):
        self.engine = engine
        self.pre = pre
        self.post = post
        self.m0 = m0

        self._cache = {}

    def cached(fn):
        @wraps(fn)
        def decorated(self, *args, **kwargs):
            cache_key = hash(tuple([fn.__name__, kwargs.values()] + list(args)))
            try:
                return self._cache[cache_key]
            except KeyError:
                self._cache[cache_key] = fn(self, *args, **kwargs)
            return self._cache[cache_key]
        return decorated

    @cached
    def filter_markings(self, markings, trans, place_name=0):
        if (markings is self.engine.zero) or (place_name >= len(self.pre[trans])):
            return markings

        if self.pre[trans][place_name] <= markings.key.tokens:
            return self.engine._make_node(
                key=markings.key,
                then_=self.filter_markings(markings.then_, trans, place_name + 1),
                else_=self.filter_markings(markings.else_, trans, place_name)
            )
        else:
            return self.filter_markings(markings.else_, trans, place_name)

    @cached
    def fire(self, markings, trans, place_name=0):
        if (markings is self.engine.zero) or (place_name >= len(self.pre[trans])):
            return markings

        if markings.key.name == place_name:
            delta = self.post[trans][place_name] - self.pre[trans][place_name]
            return self.engine._make_node(
                key=Place(
                    name=place_name,
                    tokens=markings.key.tokens + delta
                ),
                then_=self.fire(markings.then_, trans, place_name + 1),
                else_=self.fire(markings.else_, trans, place_name)
            )

        raise ValueError('Invalid family of markings.')

    def step(self, markings):
        rv = self.engine.zero
        for trans in self.pre:
            rv = rv | self.fire(self.filter_markings(markings, trans), trans)
        return rv

    def state_space(self):
        x = self.m0
        y = x | self.step(x)
        while x is not y:
            x = y
            y = x | self.step(x)
        return y


class Philosophers(PetriNet):

    def __init__(self, engine, nb_philos):
        self.nb_philos = nb_philos
        self.nb_places = 3 * nb_philos

        # Generate the pre and post functions for `nb_philos` philosophers.
        pre = {}
        post = {}
        for ph in range(self.nb_philos):
            e = [0 for _ in range(self.nb_places)]
            e[ph * 3] = 1
            e[ph * 3 + 1] = 1
            e[(ph * 3 + 4) % self.nb_places] = 1
            pre['e' + str(ph)] = e
            post['t' + str(ph)] = e

            t = [0 for _ in range(self.nb_places)]
            t[ph * 3 + 2] = 1
            pre['t' + str(ph)] = t
            post['e' + str(ph)] = t

        # Generate the initial marking for `np_philos` philosophers.
        m0 = engine.make([Place(i, 1 if i % 3 != 2 else 0) for i in range(self.nb_places)])

        # Initialize the underlying Petri Net.
        super().__init__(engine, pre, post, m0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-n', '--philosophers', dest='philosophers', action='store', default=3, type=int,
        help='The number of philosophers (default: 3).')

    args = parser.parse_args()

    engine = Engine()
    philosophers = Philosophers(engine, args.philosophers)

    start = time.time()
    state_space = philosophers.state_space()
    elapsed = time.time() - start

    print('Result of computation for %i philosophers:' % philosophers.nb_philos)
    print('\t%i state(s), computed in %f[s]' % (len(state_space), elapsed))
