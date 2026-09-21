#!/usr/bin/env python3
import unittest

from bpc_suffix_policy_v34 import ActionSuffixes


class SuffixPolicyTest(unittest.TestCase):
    def test_suffix_backoff_and_history_change_prediction(self):
        memory=ActionSuffixes(2)
        memory.observe((1,2),[(b'',0),(b'',1),(b'',2),(b'',0),(b'',1),(b'',3)])
        self.assertGreater(memory.probabilities(((1,2),),[0])[1],memory.probabilities(((1,2),),[0])[0])
        self.assertGreater(memory.probabilities(((1,2),),[0,1])[2],memory.probabilities(((1,2),),[0,1])[0])

    def test_missing_context_backs_off_without_writes(self):
        memory=ActionSuffixes(3);memory.observe((1,2),[(b'',0),(b'',1)])
        before=(memory.writes,memory.digest());p=memory.probabilities(((1,2),),[3,3,3])
        self.assertAlmostEqual(sum(p),1);self.assertEqual((memory.writes,memory.digest()),before)
