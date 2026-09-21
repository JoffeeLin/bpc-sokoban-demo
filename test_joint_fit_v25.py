#!/usr/bin/env python3
import unittest
from bpc_joint_fit_v25 import advance


class JointFitTest(unittest.TestCase):
    def test_belief_prediction_is_normalized(self):
        value=advance((.7,.3),((.9,.1),(.2,.8)));self.assertAlmostEqual(value[0],.69);self.assertAlmostEqual(sum(value),1.)


if __name__=='__main__':unittest.main()
