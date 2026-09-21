#!/usr/bin/env python3
import unittest

from bpc_responsibility_policy_v35 import norm


class ResponsibilityPolicyTest(unittest.TestCase):
    def test_norm_is_probability(self):self.assertEqual(norm([0,0,0,0]),[.25]*4);self.assertAlmostEqual(sum(norm([1,2,3,4])),1)
    def test_joint_posterior_differs_from_state_and_time_alone(self):
        state=[.7,.1,.1,.1];time=[.1,.7,.1,.1];joint=norm([a*b for a,b in zip(state,time)])
        self.assertNotEqual(joint,state);self.assertNotEqual(joint,time);self.assertAlmostEqual(sum(joint),1)
