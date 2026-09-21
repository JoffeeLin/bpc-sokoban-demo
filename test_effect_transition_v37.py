#!/usr/bin/env python3
import unittest

from bpc_effect_transition_v37 import EffectTransitions,compact_transitions


class EffectTransitionTest(unittest.TestCase):
    def test_compact_transitions_retain_after_state(self):
        a,b,c=b'a',b'b',b'c';self.assertEqual(compact_transitions([(a,0,b),(b,1,c)]),[(a,0,b),(b,1,c)])
        self.assertEqual(compact_transitions([(a,0,b),(b,1,a)]),[])
    def test_effect_changes_next_action_and_query_is_read_only(self):
        zero=bytes(6);plane0=bytes([1,0,0,0,0,0]);plane1=bytes([0,1,0,0,0,0])
        memory=EffectTransitions();memory.observe((1,2),[(zero,0,plane0),(plane0,1,zero),(zero,0,plane1),(plane1,2,zero)])
        before=(memory.writes,memory.digest());p=memory.probabilities(((1,2),),0,(0,));q=memory.probabilities(((1,2),),0,(1,))
        self.assertGreater(p[1],p[2]);self.assertGreater(q[2],q[1]);self.assertEqual((memory.writes,memory.digest()),before)
