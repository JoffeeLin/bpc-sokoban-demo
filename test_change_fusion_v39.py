#!/usr/bin/env python3
import unittest

from general_bpc_v7 import RelationalBPC,RelationalEncoder


class ChangeFusionTest(unittest.TestCase):
    def test_raw_change_beta_prefers_observed_changing_action(self):
        cube=RelationalBPC(RelationalEncoder(1,1,6));state=bytes([1,0,0,0,0,0])
        for _ in range(8):cube.observe_transition(state,0,True);cube.observe_transition(state,1,False)
        probability=cube.change_probabilities(state);self.assertGreater(probability[0],probability[1])
    def test_change_query_is_read_only(self):
        cube=RelationalBPC(RelationalEncoder(1,1,6));state=bytes([1,0,0,0,0,0]);cube.observe_transition(state,0,True);before=(cube.writes,cube.digest())
        cube.change_probabilities(state);self.assertEqual((cube.writes,cube.digest()),before)
