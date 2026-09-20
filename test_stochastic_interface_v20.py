#!/usr/bin/env python3
import random,unittest

from bpc_stochastic_interface_v20 import fit_mixture,mode_rows,sample


class StochasticInterfaceTest(unittest.TestCase):
    def test_em_recovers_observed_probability_mixture(self):
        rng=random.Random(2001);truth=(.54,.24,.14,.08);rows=[]
        for _ in range(12000):
            action=sample(truth,rng);rows.append(tuple(0. if i==action else -18. for i in range(4)))
        learned,_=fit_mixture(rows)
        self.assertLess(sum(abs(a-b) for a,b in zip(truth,learned)),.04)

    def test_mode_rows_preserve_noop_nuisance(self):
        rows=mode_rows(((.1,.6,.1,.1,.1),(.01,.01,.01,.01,.96)))
        self.assertEqual(rows[0],(0.,1.,0.,0.,0.));self.assertEqual(rows[1],(0.,0.,0.,0.,1.))


if __name__=='__main__':unittest.main()
