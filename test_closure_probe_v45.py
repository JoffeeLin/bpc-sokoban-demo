#!/usr/bin/env python3
import random,unittest

from bpc_fourth_factor_v28 import step
from bpc_three_factor_v12 import key
from closure_probe_v45 import probe,suite


class ClosureProbeTest(unittest.TestCase):
    def test_exactly_one_action_closes_boundary(self):
        for action in range(4):
            world=probe(random.Random(40+action),action);self.assertEqual([a for a in range(4) if step(world,a).marks==0],[action])
    def test_suite_is_balanced_unique_and_excludes(self):
        first,seen,_=suite(4,20);second,seen2,_=suite(5,20,seen)
        self.assertEqual([a for _,a in first].count(0),5);self.assertEqual(len(seen),20);self.assertFalse(seen&seen2);self.assertEqual({key(w) for w,_ in second},seen2)


if __name__=='__main__':unittest.main()
