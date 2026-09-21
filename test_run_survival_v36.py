#!/usr/bin/env python3
import unittest

from bpc_run_survival_v36 import RunSurvival


class RunSurvivalTest(unittest.TestCase):
    def test_survival_falls_after_observed_end(self):
        runs=RunSurvival();runs.observe((1,2),[(b'',0),(b'',0),(b'',0),(b'',1)])
        self.assertGreater(runs.probability(((1,2),),0,1),runs.probability(((1,2),),0,3))
    def test_query_is_read_only_and_factor_balanced(self):
        runs=RunSurvival();runs.observe((1,2),[(b'',0),(b'',0)]);runs.observe((1,3),[(b'',0)])
        before=(runs.writes,runs.digest());p=runs.probability(((1,2),(1,3)),0,1)
        self.assertGreater(p,0);self.assertLess(p,1);self.assertEqual((runs.writes,runs.digest()),before)
