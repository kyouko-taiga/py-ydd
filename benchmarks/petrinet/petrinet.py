# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

import xml.etree.ElementTree as ET

from functools import wraps


class Place(object):

    def __init__(self, id_, tokens=0):
        self.id_ = id_
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
        return '%s:%i' % (self.id_, self.tokens)

    def __repr__(self):
        return 'Place<%s:%i>' % (self.id_, self.tokens)


class PetriNet(object):

    def __init__(self, engine, pre, post, m0, place_names=None, place_class=Place):
        self.engine = engine
        self.pre = pre
        self.post = post
        self.m0 = m0

        self.place_names = place_names
        self.place_class = place_class

        self._cache = {
            'filter_markings': {},
            'fire': {}
        }

    def cached(fn):
        @wraps(fn)
        def decorated(self, *args, **kwargs):
            cache = self._cache[fn.__name__]
            _args = tuple([fn.__name__] + list(args))
            try:
                return cache[_args]
            except KeyError:
                rv = fn(self, *args, **kwargs)
            cache[_args] = rv
            return rv
        return decorated

    @cached
    def filter_markings(self, markings, trans, place_id=0):
        if (markings.is_zero()) or (place_id >= len(self.pre[trans])):
            return markings

        if self.pre[trans][place_id] <= markings.key.tokens:
            return self.engine.make_node(
                markings.key,
                self.filter_markings(markings.then_, trans, place_id + 1),
                self.filter_markings(markings.else_, trans, place_id))
        else:
            return self.filter_markings(markings.else_, trans, place_id)

    @cached
    def fire(self, markings, trans, place_id=0):
        if (markings.is_zero()) or (place_id >= len(self.pre[trans])):
            return markings

        if markings.key.id_ == place_id:
            delta = self.post[trans][place_id] - self.pre[trans][place_id]
            return self.engine.make_node(
                self.place_class(
                    id_=place_id,
                    tokens=markings.key.tokens + delta
                ),
                self.fire(markings.then_, trans, place_id + 1),
                self.fire(markings.else_, trans, place_id))

        raise ValueError('Invalid family of markings.')

    def step(self, markings):
        rv = self.engine.make_terminal(False)
        for trans in self.pre:
            rv = rv | self.fire(self.filter_markings(markings, trans), trans)
        return rv

    def state_space(self):
        x = self.m0
        y = x | self.step(x)
        while x != y:
            x = y
            y = x | self.step(x)
        return y

    @classmethod
    def from_pnml(cls, engine, filename, place_class=Place):
        # Parse the PNML file, stripping all namespaces.
        tree = ET.iterparse(filename)
        for _, el in tree:
                el.tag = el.tag.split('}', 1)[1]
        root = tree.root

        nets = {}
        for net_node in root:
            # Get the list of places, with their initial marking.
            places = {}
            place_names = {}
            for place_num, place_node in enumerate(net_node.iter('place')):
                try:
                    tokens = int(place_node.find('./initialMarking/text').text)
                except AttributeError:
                    tokens = 0

                places[place_node.get('id')] = place_class(place_num, tokens=tokens)
                place_names[place_node.get('id')] = place_node.find('./name/text').text

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

            nets[net_node.get('id')] = cls(
                engine, pre, post, m0, place_names=place_names, place_class=place_class)

        return nets
