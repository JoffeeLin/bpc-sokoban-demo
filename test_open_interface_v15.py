#!/usr/bin/env python3
"""Focused contracts for variable-cardinality anonymous interface binding."""
import unittest

from bpc_open_interface_v15 import (action_stats,collect_open_interface,infer_action_subset,
    infer_sensor_subset,inverse_subset)


class OpenInterfaceTest(unittest.TestCase):
    def test_unlabeled_counts_reject_extra_sensor_and_action_slots(self):
        sensors=(None,5,1,3,None,0,4,2);actions=(2,None,0,3,None,1)
        reference,triples,_=collect_open_interface(31,24,20);reference_actions=action_stats(triples,range(6),6,4)
        target,triples,_=collect_open_interface(32,{'push':48,'collect':12,'open':12},20,sensors,actions)
        channel=infer_sensor_subset(reference,target);actuator=infer_action_subset(reference_actions,action_stats(triples,channel['mapping'],8,6))
        self.assertEqual(channel['mapping'],inverse_subset(sensors,6));self.assertEqual(actuator['mapping'],inverse_subset(actions,4))


if __name__=='__main__':unittest.main()
