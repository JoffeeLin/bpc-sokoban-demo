#!/usr/bin/env python3
import random,unittest

from bpc_fourth_factor_v28 import step
from closure_orbit_v46 import orbit_suite,rotate_action,rotate_world
from closure_probe_v45 import probe


class ClosureOrbitTest(unittest.TestCase):
    def test_rotation_preserves_unique_closure_action(self):
        base=probe(random.Random(7),1)
        for turns in range(4):
            world=rotate_world(base,turns);expected=rotate_action(1,turns)
            self.assertEqual([action for action in range(4) if step(world,action).marks==0],[expected])
    def test_each_orbit_contains_every_action_and_excludes(self):
        first,seen,_=orbit_suite(8,5);second,seen2,_=orbit_suite(9,5,seen)
        self.assertEqual(sorted(action for _,action in first[:4]),list(range(4)));self.assertEqual(len(seen),20);self.assertFalse(seen&seen2)


if __name__=='__main__':unittest.main()
