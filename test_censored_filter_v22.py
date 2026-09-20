#!/usr/bin/env python3
import unittest
from bpc_censored_filter_v22 import censored_update


class CensoredFilterTest(unittest.TestCase):
    def test_no_change_advances_without_emission_update(self):
        transition=((.9,.1),(.2,.8));channels=(((.9,.04,.03,.03),)*4,((.03,.9,.04,.03),)*4)
        posterior,predicted=censored_update((.6,.4),0,b'x',b'x',None,transition,channels)
        self.assertEqual(posterior,(.6,.4));self.assertAlmostEqual(predicted[0],.62);self.assertAlmostEqual(sum(predicted),1.)


if __name__=='__main__':unittest.main()
