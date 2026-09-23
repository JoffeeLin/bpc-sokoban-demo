#!/usr/bin/env python3
import unittest

from bpc_residual_activity_v49 import ResidualActivityMedium


class ResidualActivityTest(unittest.TestCase):
    def images(self):
        cue=bytearray([64]*64);cue[0]=8;cue[-1]=129;blank=bytearray(cue);blank[0]=0;closed=bytearray(blank);closed[-1]=128
        return bytes(cue),bytes(blank),bytes(closed)
    def test_activity_is_volatile_and_persistent_query_is_read_only(self):
        cue,blank,closed=self.images();medium=ResidualActivityMedium(power=10)
        for _ in range(12):
            medium.begin();medium.advance(cue,2,blank,True);medium.advance(blank,2,closed,True)
            medium.begin();medium.advance(cue,0,blank,True);medium.advance(blank,0,blank,True)
        digest=medium.digest();writes=medium.writes;medium.begin();medium.advance(cue,2,blank);self.assertTrue(medium.activity);medium.predict_all(blank)
        self.assertEqual((medium.digest(),medium.writes),(digest,writes))
    def test_zero_flip_and_shift_are_real_activity_interventions(self):
        cue,blank,closed=self.images();medium=ResidualActivityMedium(power=10)
        for _ in range(20):
            medium.begin();medium.advance(cue,2,blank,True);medium.advance(blank,2,closed,True)
            medium.begin();medium.advance(cue,0,blank,True);medium.advance(blank,0,blank,True)
        values={}
        for mode in ('normal','zero','flip','shift'):
            medium.begin(mode);medium.advance(cue,2,blank);values[mode]=tuple(medium.probability(blank,a,63,0) for a in range(4))
        self.assertNotEqual(values['normal'],values['zero']);self.assertNotEqual(values['normal'],values['flip']);self.assertNotEqual(values['normal'],values['shift'])
    def test_action_renaming_preserves_activity_dynamics(self):
        cue,blank,closed=self.images();rename=(2,0,3,1);a=ResidualActivityMedium(power=10);b=ResidualActivityMedium(power=10)
        for action in range(4):
            after=closed if action==1 else blank
            for _ in range(3):a.begin();a.advance(cue,action,after,True);b.begin();b.advance(cue,rename[action],after,True)
        a.begin();b.begin();a.advance(cue,1,blank);b.advance(cue,rename[1],blank)
        for action in range(4):self.assertAlmostEqual(a.probability(blank,action,63,0),b.probability(blank,rename[action],63,0))


if __name__=='__main__':unittest.main()
