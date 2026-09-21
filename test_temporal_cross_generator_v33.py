#!/usr/bin/env python3
import unittest

from bpc_temporal_cross_generator_v33 import generate
from bpc_fourth_factor_v28 import shortest
from bpc_three_factor_v12 import key


class TemporalCrossGeneratorTest(unittest.TestCase):
    def test_worlds_are_unique_solvable_and_causally_joint(self):
        suite,_=generate(33,16);self.assertEqual(len({key(world) for _,world,_ in suite}),16)
        for _,world,distance in suite:
            self.assertEqual(shortest(world),distance);self.assertIsNone(shortest(world,True));self.assertIsNone(shortest(world,False,True))


if __name__=='__main__':unittest.main()
