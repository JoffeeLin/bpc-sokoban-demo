#!/usr/bin/env python3
import random,unittest

from bpc_active_probe_v27 import active_replacement,advance,change_information


class ActiveProbeTest(unittest.TestCase):
    def test_information_finds_mode_separating_slot(self):
        belief=(.5,.5);change=(.95,.05,.05,.05)
        identity=((1.,0,0,0),(0,1.,0,0),(0,0,1.,0),(0,0,0,1.))
        swapped=(identity[1],identity[0],identity[2],identity[3])
        info=change_information(belief,(identity,swapped),change)
        self.assertGreater(info[0],info[2]);self.assertGreater(info[1],info[3])

    def test_replacement_never_lowers_task_probability(self):
        p=(.1,.2,.3,.4);info=(.9,.8,.7,.6)
        for base in range(4):
            chosen,_=active_replacement(base,p,info,random.Random(1));self.assertGreaterEqual(p[chosen],p[base])

    def test_delay_prediction_normalizes(self):
        value=advance((1.,0.),((.8,.2),(.1,.9)),4)
        self.assertAlmostEqual(sum(value),1.);self.assertTrue(all(0<=x<=1 for x in value))


if __name__=='__main__':unittest.main()
