#!/usr/bin/env python3
import unittest

from bpc_event_boundary_v38 import EventBoundary


class EventBoundaryTest(unittest.TestCase):
    def test_terminal_effect_has_lower_continuation(self):
        zero=bytes(6);move=bytes([0,1,0,0,0,0]);terminal=bytes([0,1,1,0,0,0]);memory=EventBoundary()
        memory.observe((1,2),[(zero,0,move),(move,1,terminal)])
        self.assertGreater(memory.probability(((1,2),),(1,)),memory.probability(((1,2),),(1,2)))
    def test_query_is_read_only_and_inversion_is_exact(self):
        zero=bytes(6);move=bytes([0,1,0,0,0,0]);memory=EventBoundary();memory.observe((1,2),[(zero,0,move)])
        before=(memory.writes,memory.digest());p=memory.probability(((1,2),),(1,))
        self.assertAlmostEqual(memory.probability(((1,2),),(1,),'invert'),1-p);self.assertEqual((memory.writes,memory.digest()),before)
