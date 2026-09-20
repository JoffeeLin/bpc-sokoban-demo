#!/usr/bin/env python3
"""Focused contracts for anonymous raw-channel binding."""
import unittest

from bpc_channel_binding_v13 import canonicalize,collect_interface,infer_binding,inverse,permute_state


class ChannelBindingTest(unittest.TestCase):
    def test_permutation_round_trip(self):
        state=bytes(range(6))*4;permutation=(4,0,5,2,1,3)
        self.assertEqual(canonicalize(permute_state(state,permutation),inverse(permutation)),state)

    def test_unlabeled_transition_fingerprints_recover_permutation(self):
        permutation=(4,0,5,2,1,3)
        reference,_=collect_interface(13,24,20)
        target,_=collect_interface(14,{'push':12,'collect':48,'open':12},20,permutation)
        self.assertEqual(infer_binding(reference,target,'transition')['mapping'],inverse(permutation))


if __name__=='__main__':unittest.main()
