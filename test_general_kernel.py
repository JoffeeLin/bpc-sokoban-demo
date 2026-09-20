#!/usr/bin/env python3
"""Small mechanism tests; these are not an AGI benchmark."""
import unittest

from bpc_general_kernel import GeneralBPC


def relation_features(raw):
    identity,relation=raw
    return ((0,identity),(1,relation))


class GeneralKernelTests(unittest.TestCase):
    def test_unseen_identity_uses_shared_relation(self):
        model=GeneralBPC(3,relation_features)
        for identity in range(20):
            relation=identity%3
            model.observe_success([((identity,relation),relation)]*4)
        decision=model.decide(('never-seen',2))
        self.assertEqual(2,max(range(3),key=decision.choice.__getitem__))
        identity_only=model.decide(('never-seen',2),families={0})
        self.assertNotEqual(2,max(range(3),key=identity_only.choice.__getitem__))
        self.assertGreater(decision.choice[2],identity_only.choice[2]+.4)

    def test_independent_binary_channel_is_not_choice_score(self):
        model=GeneralBPC(3,relation_features,defer_below=.01)
        for _ in range(12):
            model.observe_success([(('a','same'),1)])
            model.observe_binary('changed',('a','same'),1,True)
        before=model.writes; decision=model.decide(('new','same'))
        self.assertGreater(decision.choice[1],.8)
        self.assertGreater(decision.channels['changed'][1],.8)
        self.assertFalse(decision.defer); self.assertEqual(before,model.writes)

    def test_uncertain_choice_can_defer(self):
        model=GeneralBPC(5,lambda raw:(),defer_below=.05)
        decision=model.decide(b'unknown')
        self.assertTrue(decision.defer)
        self.assertEqual((.2,)*5,decision.choice)


if __name__=='__main__': unittest.main()
