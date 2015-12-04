# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

import unittest

from ydd.ydd import Engine


class TestYDD(unittest.TestCase):

    def setUp(self):
        self.engine = Engine()

    def test_empty_family(self):
        self.assertEqual(self.engine.make_one(set()), self.engine.one)
        self.assertEqual(self.engine.make_one(list()), self.engine.one)
        self.assertEqual(self.engine.make_one(tuple()), self.engine.one)

    def test_make_one(self):
        self.assertEqual(self.engine.make_one({-1, 1}).enum(), [{-1, 1}])
        self.assertEqual(self.engine.make_one([-1, 1]).enum(), [{-1, 1}])
        self.assertEqual(self.engine.make_one((-1, 1)).enum(), [{-1, 1}])

        self.assertEqual(self.engine.make_one([-1, 1, 1]).enum(), [{-1, 1}])
        self.assertEqual(self.engine.make_one((-1, 1, 1)).enum(), [{-1, 1}])

        self.assertEqual(self.engine.make_one({-1, 1, 2}).enum(), [{-1, 1, 2}])

    def test_unicity(self):
        a = self.engine.make_one([])
        b = self.engine.make_one([])
        self.assertEqual(id(a), id(b))

        a = self.engine.make_one([1])
        b = self.engine.make_one([1])
        self.assertEqual(id(a), id(b))

        a = self.engine.make_one([-2, 0, 2])
        b = self.engine.make_one([2, -2, 0])
        self.assertEqual(id(a), id(b))

    def test_union(self):
        # Test the union of empty families.
        eue = self.engine.make_one([]) | self.engine.make_one([])
        self.assertEqual(eue.enum(), [set()])

        # Test the union of equivalent families.
        aua = self.engine.make_one({1, 3, 8}) | self.engine.make_one({1, 3, 8})
        self.assertEqual(aua.enum(), [{1, 3, 8}])

        # Test the union of identical DDs.
        dd = self.engine.make_one({1, 3, 8})
        self.assertEqual(dd | dd, dd)

        families = [
            # Test the union of overlapping families.
            ({1, 3, 9}, {1, 3, 8}),
            ({1, 3, 8}, {1, 3, 9}),
            # Test the union of disjoint families.
            ({1, 3, 9}, {0, 2, 4}),
            ({0, 2, 4}, {1, 3, 9})
        ]

        for sa, sb in families:
            a = self.engine.make_one(sa)
            b = self.engine.make_one(sb)
            aub = a | b
            bua = b | a

            self.assertEqual(
                set(frozenset(el) for el in aub.enum()),
                set(frozenset(el) for el in (sa, sb))
            )
            self.assertEqual(aub, bua)
