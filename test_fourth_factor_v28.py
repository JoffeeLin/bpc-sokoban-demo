#!/usr/bin/env python3
import random,unittest

from bpc_fourth_factor_v28 import place_world,shortest,step
from bpc_three_factor_v12 import changed_planes,raw


class FourthFactorTest(unittest.TestCase):
    def test_alcove_success_has_new_raw_signature(self):
        world=place_world(random.Random(4));self.assertIsNotNone(shortest(world))
        # Search for a shortest terminal edge and verify the model-visible signature.
        frontier=[world];seen={world};found=None
        while frontier and found is None:
            nxt=[]
            for state in frontier:
                for action in range(4):
                    after=step(state,action)
                    if after.marks==0:found=(raw(state),raw(after));break
                    if after not in seen:seen.add(after);nxt.append(after)
                if found:break
            frontier=nxt
        self.assertEqual(changed_planes(*found),(1,2,3))

    def test_object_and_gate_are_causally_required(self):
        from bpc_fourth_factor_v28 import four_factor_world
        world=four_factor_world(random.Random(7))
        self.assertIsNotNone(shortest(world));self.assertIsNone(shortest(world,True));self.assertIsNone(shortest(world,False,True))


if __name__=='__main__':unittest.main()
