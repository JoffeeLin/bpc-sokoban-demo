#!/usr/bin/env python3
"""Focused algebra checks for the v0.11 additive evidence field."""
import math,unittest

from bpc_evidence_field_v11 import normalize


class EvidenceFieldTest(unittest.TestCase):
    def test_additive_log_evidence_is_probability_product(self):
        left=[.1,.2,.3,.4];right=[.4,.3,.2,.1]
        got=normalize([.72*(math.log(x)+math.log(y)) for x,y in zip(left,right)])
        expected=[x*y for x,y in zip(left,right)];total=sum(expected);expected=[x/total for x in expected]
        for a,b in zip(got,expected):self.assertAlmostEqual(a,b)

    def test_constant_log_offset_does_not_change_choice(self):
        base=normalize([-2.,-1.,0.,1.]);shifted=normalize([x+19 for x in (-2.,-1.,0.,1.)])
        for a,b in zip(base,shifted):self.assertAlmostEqual(a,b)


if __name__=='__main__':unittest.main()
