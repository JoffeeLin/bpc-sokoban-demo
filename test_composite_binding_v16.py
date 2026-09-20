#!/usr/bin/env python3
"""Focused contracts for support-invariant composite sensor rejection."""
import unittest

from bpc_composite_binding_v16 import collect_composite_interface,infer_support_binding
from bpc_open_interface_v15 import inverse_subset


class CompositeBindingTest(unittest.TestCase):
    def test_four_unlabeled_regimes_reject_displaced_xor_planes(self):
        sensors=(4,None,0,2,5,None,3,1);actions=(None,3,1,0,None,2)
        mixes=({'push':48,'collect':12,'open':12},{'push':12,'collect':48,'open':12},
            {'push':12,'collect':12,'open':48},{'push':24,'collect':24,'open':24})
        reference,_,_,support=collect_composite_interface(51,24,20);targets=[];excluded=set()
        for index,mix in enumerate(mixes):
            target,_,initials,target_support=collect_composite_interface(52+index,mix,20,sensors,actions,excluded)
            excluded|=initials;targets.append((target,target_support))
        learned=infer_support_binding(reference,support,targets)
        self.assertEqual(learned['mapping'],inverse_subset(sensors,6))
        self.assertTrue(all(row['mapping']==learned['mapping'] for row in learned['per_stream']))


if __name__=='__main__':unittest.main()
