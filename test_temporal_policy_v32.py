#!/usr/bin/env python3
import unittest

from bpc_temporal_policy_v32 import ActionTransitions


class TemporalPolicyTest(unittest.TestCase):
    def test_factor_conditioned_bigram_and_shuffle(self):
        model=ActionTransitions();model.observe((1,2),[(b'',0),(b'',1),(b'',1)])
        row=model.probabilities(((1,2),),0);shifted=model.probabilities(((1,2),),0,1)
        self.assertEqual(max(range(4),key=row.__getitem__),1);self.assertEqual(max(range(4),key=shifted.__getitem__),2)
        self.assertAlmostEqual(sum(row),1.)

    def test_unobserved_previous_defers(self):
        model=ActionTransitions();model.observe((1,2),[(b'',0)])
        self.assertIsNone(model.probabilities(((1,2),),3))


if __name__=='__main__':unittest.main()
