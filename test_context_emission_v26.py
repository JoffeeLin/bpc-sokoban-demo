#!/usr/bin/env python3
import unittest
from bpc_context_emission_v26 import ContextEmission


class ContextEmissionTest(unittest.TestCase):
    def test_transition_logs_are_finite(self):
        profile=ContextEmission();before=bytes(294);after=bytearray(before);after[7]=1;after=bytes(after)
        for _ in range(4):profile.observe(before,1,after)
        self.assertEqual(len(profile.logs(before,after)),4);self.assertTrue(all(x==x for x in profile.logs(before,after)))


if __name__=='__main__':unittest.main()
