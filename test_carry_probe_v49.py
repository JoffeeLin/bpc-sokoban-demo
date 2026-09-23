#!/usr/bin/env python3
import random,unittest

from carry_probe_v49 import world


class CarryProbeTest(unittest.TestCase):
    def test_only_cued_action_advances_and_boundary_is_monotone(self):
        state=world(random.Random(1),2,4);initial=state.image();wrong=state.step(0)
        self.assertEqual(wrong.progress,0);self.assertEqual(wrong.image()[-1]&1,1);self.assertTrue(wrong.visible)
        state=state.step(2);self.assertEqual(state.progress,1);self.assertFalse(state.visible);self.assertEqual(state.image()[-1]&1,1)
        for _ in range(3):state=state.step(2)
        self.assertTrue(state.closed);self.assertEqual(state.image()[-1]&1,0);self.assertEqual(state.step(0).image()[-1]&1,0);self.assertNotEqual(initial,state.image())
    def test_decor_is_independent_of_cue_and_interface_shape_is_fixed(self):
        rng=random.Random(2)
        for cue in range(4):
            state=world(rng,cue,5);self.assertEqual(len(state.image()),64);self.assertEqual(state.image()[-1],129);self.assertTrue(all(0<=cell<56 for cell,_ in state.decor))


if __name__=='__main__':unittest.main()
