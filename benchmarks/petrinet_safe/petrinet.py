# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

import xml.etree.ElementTree as ET

from functools import wraps


class PetriNet(object):

    def __init__(self, engine, pre, post, m0, place_names=None):
        self.engine = engine
        self.pre = pre
        self.post = post
        self.m0 = m0

        self.place_names = place_names

        self._cache = {
            'filter_markings': {},
            'fire': {}
        }

    def cached(fn):
        @wraps(fn)
        def decorated(self, *args, **kwargs):
            cache = self._cache[fn.__name__]
            try:
                return cache[args]
            except KeyError:
                rv = fn(self, *args, **kwargs)
            cache[args] = rv
            return rv
        return decorated

    def filter_markings(self, markings, trans, place_id=0):
        # If `markings` is the zero terminal, or if we checked all the places,
        # we can return the markings unmodified.
        if markings.is_zero() or (place_id >= len(self.pre[trans])):
            return markings

        # If a token is required in the place identified by `place_id`, we've
        # to ensure `place_id` appears in the accepting paths. If `markings`
        # is the accepting terminal, or starts with a greater key, we know it
        # doesn't. If it has the same key, then we can reject all paths from
        # its `else` child. If it as a lower key, we should continue on both
        # its children.
        if self.pre[trans][place_id]:
            if markings.is_one() or (markings.key > place_id):
                return self.engine.make_terminal(False)
            if markings.key == place_id:
                return self.engine.make_node(
                    place_id,
                    self.filter_markings(markings.then_, trans, place_id + 1),
                    self.engine.make_terminal(False))
            if markings.key < place_id:
                return self.engine.make_node(
                    markings.key,
                    self.filter_markings(markings.then_, trans, place_id),
                    self.filter_markings(markings.else_, trans, place_id))

        # If no token is required in the place identified by `place_id`, we've
        # to continue with the next place ID.
        return self.filter_markings(markings, trans, place_id + 1)

    def fire(self, markings, trans, place_id=0):
        # If `markings` is the zero terminal, or if we checked all the places,
        # we can return the markings unmodified.
        if (markings.is_zero()) or (place_id >= len(self.pre[trans])):
            return markings

        delta = self.post[trans][place_id] - self.pre[trans][place_id]

        # If we have to produce a token in the place identified by `place_id`,
        # then we insert it "in-place" if `markings` is terminal or starts
        # with a greater key, otherwise we continue the recursion on both its
        # children. Other cases shouldn't occur.
        if delta > 0:
            if markings.is_one() or (markings.key > place_id):
                return self.engine.make_node(
                    place_id,
                    self.fire(markings, trans, place_id + 1),
                    self.engine.make_terminal(False))
            if markings.key < place_id:
                return self.engine.make_node(
                    markings.key,
                    self.fire(markings.then_, trans, place_id),
                    self.fire(markings.else_, trans, place_id))

            raise ValueError('Invalid set of markings')

        # If we have to consume a token in the place identified by `place_id`,
        # then we return then "then" child of `markings` if its key is equal
        # to `place_id`, otherwise we continue the recursion on both its
        # children. Other cases shouldn't occur.
        elif delta < 0:
            if markings.key == place_id:
                return self.fire(markings.then_, trans, place_id + 1)
            if markings.key < place_id:
                return self.engine.make_node(
                    markings.key,
                    self.fire(markings.then_, trans, place_id),
                    self.fire(markings.else_, trans, place_id))

            raise ValueError('Invalid set of markings')

        # If no token is either produced or consumed for the place identified
        # by `place_id`, we've to continue with the next place ID.
        return self.fire(markings, trans, place_id + 1)

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
    def from_pnml(cls, engine, filename):
        # Parse the PNML file, stripping all namespaces.
        tree = ET.iterparse(filename)
        for _, el in tree:
                el.tag = el.tag.split('}', 1)[1]
        root = tree.root

        nets = {}
        for net_node in root:
            # Get the list of places, with their initial marking.
            num_from_id = {}
            tokens_from_num = {}

            place_names = {}
            nb_of_places = 0
            for place_num, place_node in enumerate(net_node.iter('place')):
                try:
                    tokens = int(place_node.find('./initialMarking/text').text)
                except AttributeError:
                    tokens = 0

                # Make sure the given Petri Net is 1-safe.
                if tokens > 1:
                    raise ValueError('pnml file contains net that is not 1-safe.')

                num_from_id[place_node.get('id')] = place_num
                tokens_from_num[place_num] = tokens
                place_names[place_num] = place_node.find('./name/text').text

            m0 = engine.make([num for (num, tokens) in tokens_from_num.items() if tokens > 0])

            # Get the list of transitions.
            transitions = {}
            for transition_node in net_node.iter('transition'):
                transitions[transition_node.get('id')] = transition_node.find('./name/text').text

            # Build the pre/post functions.
            pre = {t: [0] * len(tokens_from_num) for t in transitions.values()}
            post = {t: [0] * len(tokens_from_num) for t in transitions.values()}
            for arc_node in net_node.iter('arc'):
                source = arc_node.get('source')
                target = arc_node.get('target')

                try:
                    tokens = int(arc_node.find('./inscription/text').text)
                except AttributeError:
                    tokens = 1

                # Identify whether the arc represents a pre- or post-condition.
                if source in num_from_id:
                    pre[transitions[target]][num_from_id[source]] = tokens
                else:
                    post[transitions[source]][num_from_id[target]] = tokens

            nets[net_node.get('id')] = cls(
                engine, pre, post, m0, place_names=place_names)

        return nets
