# Copyright (c) 2015, Dimitri Racordon.
# Licensed under the Apache License, Version 2.0.

import unittest

from ydd.engines.cpp import IntEngine


class TestIntEngine(unittest.TestCase):

    def setUp(self):
        self.engine = IntEngine()

    def test_make_terminal(self):
        self.assertTrue(self.engine.make_terminal(False).is_zero())
        self.assertTrue(self.engine.make_terminal(True).is_one())

    def test_make_node(self):
        zero = self.engine.make_terminal(False)
        one = self.engine.make_terminal(True)

        a = self.engine.make_node(1, one, zero)
        self.assertEqual(a.key, 1)
        self.assertEqual(a.then_, one)
        self.assertEqual(a.else_, zero)

        b = self.engine.make_node(0, one, a)
        self.assertEqual(b.key, 0)
        self.assertEqual(b.then_, one)
        self.assertEqual(b.else_, a)

    def test_make_from_container(self):
        self.assertTrue(self.engine.make(set()).is_one())
        self.assertTrue(self.engine.make([]).is_one())

        self.assertEqual(list(self.engine.make_from_container({-1, 1})), [{-1, 1}])
        self.assertEqual(list(self.engine.make_from_container([-1, 1])), [{-1, 1}])

        self.assertEqual(list(self.engine.make_from_container({-1, 1, 1})), [{-1, 1}])
        self.assertEqual(list(self.engine.make_from_container([-1, 1, 1])), [{-1, 1}])

        self.assertEqual(list(self.engine.make_from_container({-1, 1, 2})), [{-1, 1, 2}])
        self.assertEqual(list(self.engine.make_from_container([-1, 1, 2])), [{-1, 1, 2}])

    def test_make(self):
        zero = self.engine.make_terminal(False)
        one = self.engine.make_terminal(True)

        self.assertEqual(self.engine.make(), zero)
        self.assertEqual(self.engine.make(set()), one)
        self.assertEqual(list(self.engine.make({1, 2})), [{1, 2}])

        family = self.engine.make({4}, {4, 5}, {4, 6, 9})
        self.assertEqual(
            set(frozenset(el) for el in family),
            set(frozenset(el) for el in ({4}, {4, 5}, {4, 6, 9}))
        )

        family = self.engine.make({4, 5}, {4, 5}, {4, 6, 9})
        self.assertEqual(
            set(frozenset(el) for el in family),
            set(frozenset(el) for el in ({4, 5}, {4, 6, 9}))
        )

    def test_equality(self):
        a = self.engine.make()
        b = self.engine.make()
        self.assertEqual(a, b)

        a = self.engine.make(set())
        b = self.engine.make(set())
        self.assertEqual(a, b)

        a = self.engine.make({1})
        b = self.engine.make({1})
        self.assertEqual(a, b)

        a = self.engine.make({-2, 0, 2})
        b = self.engine.make({2, -2, 0})
        self.assertEqual(a, b)

        a = self.engine.make({4, 5}, {4}, {4, 6, 9})
        b = self.engine.make({4}, {4, 6, 9}, {4, 5})
        self.assertEqual(a, b)

    def test_contains(self):
        family = self.engine.make_terminal(False)
        self.assertFalse(set() in family)

        family = self.engine.make_terminal(True)
        self.assertTrue(set() in family)
        self.assertFalse({1} in family)

        family = self.engine.make({1})
        self.assertTrue({1} in family)
        self.assertFalse(set() in family)
        self.assertFalse({2} in family)

        family = self.engine.make({1, 2}, {1, 3}, {4, 5})
        self.assertTrue({1, 2} in family)
        self.assertTrue({1, 3} in family)
        self.assertTrue({4, 5} in family)

        self.assertFalse(set() in family)
        self.assertFalse({1} in family)
        self.assertFalse({1, 5} in family)

    def test_iter(self):
        family = self.engine.make_terminal(False)
        self.assertEqual(list(family), [])

        family = self.engine.make_terminal(True)
        self.assertEqual(list(family), [set()])

        family = self.engine.make({1})
        self.assertEqual(list(family), [{1}])

        family = self.engine.make({1, 2})
        self.assertEqual(list(family), [{1, 2}])

        family = self.engine.make({4}, {4, 5}, {4, 6, 9})
        self.assertEqual(
            set(frozenset(el) for el in family),
            set(frozenset(el) for el in ({4}, {4, 5}, {4, 6, 9}))
        )

    def test_len(self):
        self.assertEqual(len(self.engine.make_terminal(False)), 0)
        self.assertEqual(len(self.engine.make_terminal(True)), 1)
        self.assertEqual(len(self.engine.make({1, 2})), 1)
        self.assertEqual(len(self.engine.make({4}, {4, 5}, {4, 6, 9})), 3)

    def test_lt(self):
        zero = self.engine.make_terminal(False)
        one = self.engine.make_terminal(True)

        # Test the inclusion of the empty family.
        family = zero
        self.assertFalse(family < zero)
        self.assertTrue(family < one)
        self.assertTrue(family < self.engine.make([1, 2]))
        self.assertTrue(family < self.engine.make([4], [4, 5], [4, 6, 9]))

        # Test the inclusion of the familiy of empty set.
        family = one
        self.assertFalse(family < zero)
        self.assertFalse(family < one)
        self.assertFalse(family < self.engine.make([1, 2]))
        self.assertFalse(family < self.engine.make([4], [4, 5], [4, 6, 9]))

        # Test the inclusion of a family of a singleton.
        family = self.engine.make([4, 5])
        self.assertFalse(family < zero)
        self.assertFalse(family < one)
        self.assertFalse(family < self.engine.make([4, 5]))
        self.assertTrue(family < self.engine.make([4], [4, 5], [4, 6, 9]))

        # Test the inclusion of an arbitrary family.
        family = self.engine.make([4, 5], [4, 6, 9])
        self.assertFalse(family < zero)
        self.assertFalse(family < one)
        self.assertFalse(family < self.engine.make([4, 5], [4, 6, 9]))
        self.assertTrue(family < self.engine.make([4], [4, 5], [4, 6, 9]))

    def test_le(self):
        zero = self.engine.make_terminal(False)
        one = self.engine.make_terminal(True)

        # Test the inclusion of the empty family.
        family = zero
        self.assertTrue(family <= zero)
        self.assertTrue(family <= one)
        self.assertTrue(family <= self.engine.make([1, 2]))
        self.assertTrue(family <= self.engine.make([4], [4, 5], [4, 6, 9]))

        # Test the inclusion of the familiy of empty set.
        family = one
        self.assertFalse(family <= zero)
        self.assertTrue(family <= one)
        self.assertFalse(family <= self.engine.make([1, 2]))
        self.assertFalse(family <= self.engine.make([4], [4, 5], [4, 6, 9]))

        # Test the inclusion of a family of a singleton.
        family = self.engine.make([4, 5])
        self.assertFalse(family <= zero)
        self.assertFalse(family <= one)
        self.assertTrue(family <= self.engine.make([4, 5]))
        self.assertTrue(family <= self.engine.make([4], [4, 5], [4, 6, 9]))

        # Test the inclusion of an arbitrary family.
        family = self.engine.make([4, 5], [4, 6, 9])
        self.assertFalse(family <= zero)
        self.assertFalse(family <= one)
        self.assertTrue(family <= self.engine.make([4, 5], [4, 6, 9]))
        self.assertTrue(family <= self.engine.make([4], [4, 5], [4, 6, 9]))

    def test_union(self):
        # Test the union of families of empty set.
        eue = self.engine.make([]) | self.engine.make([])
        self.assertEqual(list(eue), [set()])

        # Test the union of identical families.
        family = self.engine.make({1, 3, 8})
        self.assertEqual(family | family, family)

        families = [
            # Test the union of families with overlapping elements.
            ({1, 3, 9}, {1, 3, 8}),
            ({1, 3, 8}, {1, 3, 9}),
            # Test the union of families with disjoint elements.
            ({1, 3, 9}, {0, 2, 4}),
            ({0, 2, 4}, {1, 3, 9})
        ]

        for fa, fb in families:
            a = self.engine.make(fa)
            b = self.engine.make(fb)
            aub = a | b
            bua = b | a

            self.assertEqual(
                set(frozenset(el) for el in aub),
                set(frozenset(el) for el in (fa, fb))
            )
            self.assertEqual(aub, bua)

    def test_intersection(self):
        # Test the intersection of families of empty set.
        eie = self.engine.make([]) & self.engine.make([])
        self.assertEqual(list(eie), [set()])

        # Test the intersection of identical families.
        family = self.engine.make({1, 3, 8}, {0, 2, 4})
        self.assertEqual(family & family, family)

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
        ede = self.engine.make([]) - self.engine.make([])
        self.assertEqual(list(ede), [])

        # Test the difference between identical families.
        family = self.engine.make({1, 3, 8}, {0, 2, 4})
        self.assertEqual(list(family - family), [])

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
        ede = self.engine.make([]) ^ self.engine.make([])
        self.assertEqual(list(ede), [])

        # Test the symmetric difference between identical families.
        family = self.engine.make({1, 3, 8}, {0, 2, 4})
        self.assertEqual(list(family ^ family), [])

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
