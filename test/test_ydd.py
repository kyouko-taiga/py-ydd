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

    def test_make_one(self):
        self.assertEqual(list(self.engine.make_one({-1, 1})), [{-1, 1}])
        self.assertEqual(list(self.engine.make_one([-1, 1])), [{-1, 1}])
        self.assertEqual(list(self.engine.make_one((-1, 1))), [{-1, 1}])

        self.assertEqual(list(self.engine.make_one([-1, 1, 1])), [{-1, 1}])
        self.assertEqual(list(self.engine.make_one((-1, 1, 1))), [{-1, 1}])

        self.assertEqual(list(self.engine.make_one({-1, 1, 2})), [{-1, 1, 2}])

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

    def test_contains(self):
        dd = self.engine.one
        self.assertTrue(set() in dd)
        self.assertTrue(list() in dd)

        dd = self.engine.zero
        self.assertFalse(set() in dd)
        self.assertFalse(list() in dd)

        dd = self.engine.make({1})
        self.assertTrue({1} in dd)
        self.assertFalse({2} in dd)

        dd = self.engine.make({1, 2}, {1, 3}, {4, 5})
        self.assertTrue({1, 2} in dd)
        self.assertTrue({1, 3} in dd)
        self.assertTrue({4, 5} in dd)

        self.assertFalse(set() in dd)
        self.assertFalse({1} in dd)
        self.assertFalse({1, 5} in dd)

    def test_union(self):
        # Test the union of families of empty set.
        eue = self.engine.make_one([]) | self.engine.make_one([])
        self.assertEqual(list(eue), [set()])

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
                set(frozenset(el) for el in aub),
                set(frozenset(el) for el in (fa, fb))
            )
            self.assertEqual(aub, bua)

    def test_intersection(self):
        # Test the intersection of families of empty set.
        eie = self.engine.make_one([]) & self.engine.make_one([])
        self.assertEqual(list(eie), [set()])

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

            self.assertEqual(list(aib), [{1, 3, 9}])
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

            self.assertEqual(list(aib), [])
            self.assertEqual(aib, bia)

    def test_difference(self):
        # Test the difference between 2 families of empty set.
        ede = self.engine.make_one([]) - self.engine.make_one([])
        self.assertEqual(list(ede), [])

        # Test the difference between identical DDs.
        dd = self.engine.make({1, 3, 8}, {0, 2, 4})
        self.assertEqual(list(dd - dd), [])

        # Test the difference between overlapping families.
        a = self.engine.make({1, 3, 9}, {0, 2, 4})
        b = self.engine.make({1, 3, 9}, {5, 6, 7})
        self.assertEqual(list(a - b), [{0, 2, 4}])

        # Test the difference between disjoint families.
        a = self.engine.make({1, 3, 9}, {0, 2, 4})
        b = self.engine.make({1, 3, 0}, {5, 6, 7})
        self.assertEqual(
            set(frozenset(el) for el in (a - b)),
            set([frozenset({1, 3, 9}), frozenset({0, 2, 4})])
        )

    def test_symmetric_difference(self):
        # Test the symmetric difference between 2 families of empty set.
        ede = self.engine.make_one([]) ^ self.engine.make_one([])
        self.assertEqual(list(ede), [])

        # Test the symmetric difference between identical DDs.
        dd = self.engine.make({1, 3, 8}, {0, 2, 4})
        self.assertEqual(list(dd ^ dd), [])

        # Test the difference between overlapping families.
        a = self.engine.make({1, 3, 9}, {0, 2, 4})
        b = self.engine.make({1, 3, 9}, {5, 6, 7})
        self.assertEqual(
            set(frozenset(el) for el in (a ^ b)),
            set([frozenset({0, 2, 4}), frozenset({5, 6, 7})])
        )

        # Test the difference between disjoint families.
        a = self.engine.make({1, 3, 9}, {0, 2, 4})
        b = self.engine.make({1, 3, 0}, {5, 6, 7})
        self.assertEqual(
            set(frozenset(el) for el in (a ^ b)),
            set(frozenset(el) for el in [{1, 3, 9}, {0, 2, 4}, {1, 3, 0}, {5, 6, 7}])
        )
