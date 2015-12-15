import argparse
import time
import sys
import xml.etree.ElementTree as ET

from functools import wraps

from ydd.ydd import Engine


class Place(object):

    def __init__(self, id_, label=None, tokens=0):
        self.id_ = id_
        self.label = label or id_
        self.tokens = tokens

    def __lt__(self, other):
        if self.id_ == other.id_:
            return self.tokens < other.tokens
        else:
            return self.id_ < other.id_

    def __eq__(self, other):
        return (self.id_ == other.id_) and (self.tokens == other.tokens)

    def __hash__(self):
        return hash((self.id_, self.tokens))

    def __str__(self):
        return '%s:%i' % (self.label, self.tokens)

    def __repr__(self):
        return 'Place<%s:%i>' % (self.label, self.tokens)


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
    def filter_markings(self, markings, trans, place_id=0):
        if (markings is self.engine.zero) or (place_id >= len(self.pre[trans])):
            return markings

        if self.pre[trans][place_id] <= markings.key.tokens:
            return self.engine._make_node(
                key=markings.key,
                then_=self.filter_markings(markings.then_, trans, place_id + 1),
                else_=self.filter_markings(markings.else_, trans, place_id)
            )
        else:
            return self.filter_markings(markings.else_, trans, place_id)

    @cached
    def fire(self, markings, trans, place_id=0):
        if (markings is self.engine.zero) or (place_id >= len(self.pre[trans])):
            return markings

        if markings.key.id_ == place_id:
            delta = self.post[trans][place_id] - self.pre[trans][place_id]
            return self.engine._make_node(
                key=Place(
                    id_=place_id,
                    tokens=markings.key.tokens + delta
                ),
                then_=self.fire(markings.then_, trans, place_id + 1),
                else_=self.fire(markings.else_, trans, place_id)
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

    @classmethod
    def from_pnml(cls, engine, filename):
        # Parse the PNML file, stripping all namespaces.
        tree = ET.iterparse(filename)
        for _, el in tree:
                el.tag = el.tag.split('}', 1)[1]
        root = tree.root

        nets = {}
        for net_node in root:
            # Get the list of places, with their initial marking.
            places = {}
            for place_num, place_node in enumerate(net_node.iter('place')):
                try:
                    tokens = int(place_node.find('./initialMarking/text').text)
                except AttributeError:
                    tokens = 0

                places[place_node.get('id')] = Place(
                    place_num,
                    label=place_node.find('./name/text').text,
                    tokens=tokens
                )

            m0 = engine.make(places.values())

            # Get the list of transitions.
            transitions = {}
            for transition_node in net_node.iter('transition'):
                transitions[transition_node.get('id')] = transition_node.find('./name/text').text

            # Build the pre/post functions.
            pre = {t: [0] * len(places) for t in transitions.values()}
            post = {t: [0] * len(places) for t in transitions.values()}
            for arc_node in net_node.iter('arc'):
                source = arc_node.get('source')
                target = arc_node.get('target')

                try:
                    tokens = int(arc_node.find('./inscription/text').text)
                except AttributeError:
                    tokens = 1

                # Identify whether the arc represents a pre- or post-condition.
                if source in places:
                    pre[transitions[target]][places[source].id_] = tokens
                else:
                    post[transitions[source]][places[target].id_] = tokens

            nets[net_node.get('id')] = cls(engine, pre, post, m0)

        return nets


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pnml', metavar='pnml', help='The filename of the PNML file to parse.')
    parser.add_argument(
        '-r', '--recursion-limit', dest='recursion', metavar='N', type=int,
        help="Override Python's default recursion limit.")
    args = parser.parse_args()

    # Set the recursion limit.
    if args.recursion:
        sys.setrecursionlimit(args.recursion)

    engine = Engine()
    pns = PetriNet.from_pnml(engine, args.pnml)

    print('%i Petri Net(s) found in the pnml file.' % len(pns))

    for id_, pn in pns.items():
        print('Generate the state space for "%s".' % id_)
        start = time.time()
        state_space = pn.state_space()
        elapsed = time.time() - start
        print('\t%i state(s), computed in %f[s]' % (len(state_space), elapsed))
