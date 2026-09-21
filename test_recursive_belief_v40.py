#!/usr/bin/env python3
import unittest

from bpc_recursive_belief_v40 import FactorEmissions,norm


class RecursiveBeliefTest(unittest.TestCase):
    def test_emission_is_factor_and_action_conditioned_and_read_only(self):
        zero=bytes(6);move=bytes([0,1,0,0,0,0]);push=bytes([0,1,1,0,0,0]);model=FactorEmissions()
        model.observe((1,2),[(zero,0,push)]);model.observe((1,3),[(zero,0,move)])
        before=(model.writes,model.digest());self.assertGreater(model.probability((1,2),0,(1,2)),model.probability((1,3),0,(1,2)));self.assertEqual((model.writes,model.digest()),before)
    def test_norm_handles_empty_probability_mass(self):
        self.assertEqual(norm([0,0,0],3),[1/3]*3);self.assertAlmostEqual(sum(norm([1,2,3],3)),1.)


if __name__=='__main__':unittest.main()
