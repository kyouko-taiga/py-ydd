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

        # Test the union of identical DDs.
        dd = self.engine.make_one({1, 3, 8})
        self.assertEqual(dd | dd, dd)

        families = [
            # Test the union of families with overlapping elements.
            ({1, 3, 9}, {1, 3, 8}),
            ({1, 3, 8}, {1, 3, 9}),
            # Test the union of families with disjoint elements.
            ({1, 3, 9}, {0, 2, 4}),
            ({0, 2, 4}, {1, 3, 9})
        ]

        for fa, fb in families:
            a = self.engine.make_one(fa)
            b = self.engine.make_one(fb)
            aub = a | b
            bua = b | a

            self.assertEqual(
                set(frozenset(el) for el in aub.enum()),
                set(frozenset(el) for el in (fa, fb))
            )
            self.assertEqual(aub, bua)

    def test_intersection(self):
        # Test the intersection of empty families.
        eie = self.engine.make_one([]) & self.engine.make_one([])
        self.assertEqual(eie.enum(), [set()])

        # Test the intersection of identical DDs.
        dd = self.engine.make({1, 3, 8}, {0, 2, 4})
        self.assertEqual(dd & dd, dd)

        # Test the intersection of overlapping families.
        families = [
            ([{1, 3, 9}, {0, 2, 4}], [{1, 3, 9}, {5, 6, 7}]),
            ([{1, 3, 9}, {5, 6, 7}], [{1, 3, 9}, {0, 2, 4}])
        ]

        for fa, fb in families:
            a = self.engine.make(*fa)
            b = self.engine.make(*fb)
            aib = a & b
            bia = b & a

            self.assertEqual(aib.enum(), [{1, 3, 9}])
            self.assertEqual(aib, bia)

        # Test the intersection of disjoint families.
        families = [
            ([{1, 3, 9}, {0, 2, 4}], [{1, 3, 0}, {5, 6, 7}]),
            ([{1, 3, 0}, {5, 6, 7}], [{1, 3, 9}, {0, 2, 4}])
        ]

        for fa, fb in families:
            a = self.engine.make(*fa)
            b = self.engine.make(*fb)
            aib = a & b
            bia = b & a

            self.assertEqual(aib.enum(), [])
            self.assertEqual(aib, bia)

    def test_difference(self):
        # Test the difference between 2 empty families.
        ede = self.engine.make_one([]) - self.engine.make_one([])
        self.assertEqual(ede.enum(), [])

        # Test the difference between identical DDs.
        dd = self.engine.make({1, 3, 8}, {0, 2, 4})
        self.assertEqual((dd - dd).enum(), [])

        # Test the difference between overlapping families.
        a = self.engine.make({1, 3, 9}, {0, 2, 4})
        b = self.engine.make({1, 3, 9}, {5, 6, 7})
        self.assertEqual((a - b).enum(), [{0, 2, 4}])

        # Test the difference between disjoint families.
        a = self.engine.make({1, 3, 9}, {0, 2, 4})
        b = self.engine.make({1, 3, 0}, {5, 6, 7})
        self.assertEqual(
            set(frozenset(el) for el in (a - b).enum()),
            set([frozenset({1, 3, 9}), frozenset({0, 2, 4})])
        )

    def test_symmetric_difference(self):
        # Test the symmetric difference between 2 empty families.
        ede = self.engine.make_one([]) ^ self.engine.make_one([])
        self.assertEqual(ede.enum(), [])

        # Test the symmetric difference between identical DDs.
        dd = self.engine.make({1, 3, 8}, {0, 2, 4})
        self.assertEqual((dd ^ dd).enum(), [])

        # Test the difference between overlapping families.
        a = self.engine.make({1, 3, 9}, {0, 2, 4})
        b = self.engine.make({1, 3, 9}, {5, 6, 7})
        self.assertEqual(
            set(frozenset(el) for el in (a ^ b).enum()),
            set([frozenset({0, 2, 4}), frozenset({5, 6, 7})])
        )

        # Test the difference between disjoint families.
        a = self.engine.make({1, 3, 9}, {0, 2, 4})
        b = self.engine.make({1, 3, 0}, {5, 6, 7})
        self.assertEqual(
            set(frozenset(el) for el in (a ^ b).enum()),
            set(frozenset(el) for el in [{1, 3, 9}, {0, 2, 4}, {1, 3, 0}, {5, 6, 7}])
        )
