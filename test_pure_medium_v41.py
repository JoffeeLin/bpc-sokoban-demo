#!/usr/bin/env python3
import unittest
from types import SimpleNamespace

from bpc_pure_medium_v41 import CELLS,PROJECTIONS,ResidualMedium,canvas,local


class PureMediumTest(unittest.TestCase):
    def test_camera_is_anonymous_fixed_canvas_with_boundary_bit(self):
        world=SimpleNamespace(h=1,w=1,walls=1,agent=0,objects=0,marks=1,switches=0,gates=0)
        row=canvas(world);self.assertEqual(len(row),CELLS);self.assertEqual(row[0],11);self.assertEqual(row[49],64);self.assertEqual(row[-1],129)
    def test_residual_write_changes_prediction_and_query_is_read_only(self):
        before=bytes(CELLS);after=bytes([1])*CELLS;medium=ResidualMedium(power=8)
        p0=medium.probability(before,2,0,0);medium.observe(before,2,after);snapshot=(medium.writes,medium.digest());p1=medium.probability(before,2,0,0)
        self.assertGreater(p1,p0);self.assertEqual((medium.writes,medium.digest()),snapshot)
    def test_action_ablation_receives_same_observation_but_cannot_separate_actions(self):
        before=bytes(CELLS);one=bytes([1])+bytes(CELLS-1);zero=bytes(CELLS);medium=ResidualMedium(power=10,use_action=False)
        medium.observe(before,0,one);medium.observe(before,1,zero)
        self.assertEqual(medium.probability(before,0,0,0),medium.probability(before,1,0,0))
    def test_parallel_output_is_fixed_typed_probability_tensor(self):
        output=ResidualMedium(power=8).predict_all(bytes(CELLS))
        self.assertEqual((len(output),len(output[0]),len(output[0][0])),(4,CELLS,8))
        self.assertTrue(all(0.0<=p<=1.0 for action in output for cell in action for p in cell))
    def test_physical_neighborhood_and_action_renaming_are_equivariant(self):
        image=bytes(range(CELLS));self.assertEqual(local(image,9,PROJECTIONS[-1]),bytes((0,1,2,8,9,10,16,17,18)))
        before=bytes(CELLS);after=bytes([1])+bytes(CELLS-1);a=ResidualMedium(power=10);b=ResidualMedium(power=10);permutation=(2,0,3,1)
        for action in range(4):a.observe(before,action,after);b.observe(before,permutation[action],after)
        for action in range(4):self.assertEqual(a.probability(before,action,0,0),b.probability(before,permutation[action],0,0))


if __name__=='__main__':unittest.main()
