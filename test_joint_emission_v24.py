#!/usr/bin/env python3
import unittest
from bpc_joint_emission_v24 import JointEffectProfiles


class JointEmissionTest(unittest.TestCase):
    def test_observed_joint_effect_prefers_its_action(self):
        profile=JointEffectProfiles();before=bytes(294);a=bytearray(before);a[1]=1;after=bytes(a)
        for _ in range(8):profile.observe(before,2,after)
        for action in (0,1,3):profile.observe(before,action,before)
        logs=profile.logs(before,after);self.assertEqual(max(range(4),key=logs.__getitem__),2)


if __name__=='__main__':unittest.main()
