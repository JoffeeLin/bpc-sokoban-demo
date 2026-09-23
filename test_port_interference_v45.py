#!/usr/bin/env python3
import unittest

from bpc_port_interference_v45 import PortInterferenceMedium
from bpc_pure_medium_v41 import CELLS


class PortInterferenceTest(unittest.TestCase):
    def test_remote_sensor_pattern_changes_port_probability(self):
        left=bytearray([64]*CELLS);right=bytearray(left);left[0]=2;right[0]=8;left[-1]=right[-1]=129
        closed_left=bytearray(left);closed_left[-1]=128
        medium=PortInterferenceMedium(power=12)
        for _ in range(12):medium.observe(bytes(left),0,bytes(closed_left));medium.observe(bytes(right),0,bytes(right))
        self.assertLess(medium.probability(bytes(left),0,CELLS-1,0),medium.probability(bytes(right),0,CELLS-1,0))
    def test_action_renaming_is_exact_and_query_read_only(self):
        before=bytearray([64]*CELLS);before[0]=10;before[-1]=129;closed=bytearray(before);closed[-1]=128;rename=(2,0,3,1);a=PortInterferenceMedium(power=12);b=PortInterferenceMedium(power=12)
        for action in range(4):
            after=closed if action in (0,3) else before
            for _ in range(action+2):a.observe(bytes(before),action,bytes(after));b.observe(bytes(before),rename[action],bytes(after))
        digest=a.digest()
        for action in range(4):self.assertEqual(a.probability(bytes(before),action,CELLS-1,0),b.probability(bytes(before),rename[action],CELLS-1,0))
        self.assertEqual(a.digest(),digest)
    def test_action_removed_control_cannot_separate_actions(self):
        before=bytearray([64]*CELLS);before[0]=2;before[-1]=129;closed=bytearray(before);closed[-1]=128;medium=PortInterferenceMedium(power=12,use_action=False)
        medium.observe(bytes(before),0,bytes(closed));medium.observe(bytes(before),1,bytes(before))
        self.assertEqual(medium.probability(bytes(before),0,CELLS-1,0),medium.probability(bytes(before),3,CELLS-1,0))


if __name__=='__main__':unittest.main()
