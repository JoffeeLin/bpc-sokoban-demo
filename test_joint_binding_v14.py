#!/usr/bin/env python3
"""Focused contracts for joint anonymous sensor and actuator binding."""
import unittest

from bpc_channel_binding_v13 import infer_binding,inverse
from bpc_joint_binding_v14 import action_stats,collect_joint_interface,infer_action_binding,inverse_action


class JointBindingTest(unittest.TestCase):
    def test_shifted_unlabeled_transitions_recover_both_interfaces(self):
        sensor=(5,3,0,4,1,2);actuator=(2,0,3,1)
        reference,triples,_=collect_joint_interface(21,24,20);reference_actions=action_stats(triples,range(6))
        target,triples,_=collect_joint_interface(22,{'push':48,'collect':12,'open':12},20,sensor,actuator)
        channels=infer_binding(reference,target,'transition');actions=infer_action_binding(reference_actions,action_stats(triples,channels['mapping']))
        self.assertEqual(channels['mapping'],inverse(sensor));self.assertEqual(actions['mapping'],inverse_action(actuator))


if __name__=='__main__':unittest.main()
