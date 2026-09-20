#!/usr/bin/env python3
import unittest

from bpc_hidden_mode_v21 import forward_backward,stationary,update_belief


class HiddenModeTest(unittest.TestCase):
    def test_forward_backward_probabilities_normalize(self):
        records=((0,(0.,-8.,-8.,-8.)),(0,(-8.,0.,-8.,-8.)),(0,(0.,-8.,-8.,-8.)))
        initial=(.5,.5);transition=((.9,.1),(.2,.8));channels=(((.97,.01,.01,.01),)*4,((.01,.97,.01,.01),)*4)
        gamma,xi,value=forward_backward(records,initial,transition,channels)
        self.assertTrue(value<0);self.assertTrue(all(abs(sum(row)-1)<1e-9 for row in gamma));self.assertTrue(all(abs(sum(map(sum,row))-1)<1e-9 for row in xi))

    def test_online_evidence_changes_belief_then_predicts(self):
        channels=(((.97,.01,.01,.01),)*4,((.01,.97,.01,.01),)*4);transition=((.9,.1),(.2,.8))
        posterior,predicted=update_belief((.5,.5),0,(0.,-10.,-10.,-10.),transition,channels)
        self.assertGreater(posterior[0],.95);self.assertGreater(predicted[0],predicted[1]);self.assertAlmostEqual(sum(predicted),1.)
        self.assertAlmostEqual(sum(stationary(transition)),1.)


if __name__=='__main__':unittest.main()
