#!/usr/bin/env python3
import random,unittest

from bpc_spatial_interface_v18 import (GaugeAveragedPolicy,TRANSFORMS,gauge_equivalent_mapping,spatial_expose,spatial_restore,
    transform_xy,transformed_delta)


class SpatialInterfaceTest(unittest.TestCase):
    def test_all_d4_transforms_are_unique_and_round_trip(self):
        state=bytes(range(49));images=[]
        for transform in range(TRANSFORMS):
            observed=spatial_expose(state,1,transform);images.append(observed);self.assertEqual(spatial_restore(observed,1,transform),state)
        self.assertEqual(len(set(images)),8)

    def test_each_transform_is_a_cell_permutation(self):
        for transform in range(TRANSFORMS):
            cells={transform_xy(x,y,transform) for y in range(7) for x in range(7)}
            self.assertEqual(len(cells),49)

    def test_every_gauge_has_one_behaviorally_equivalent_action_injection(self):
        actual_mapping=(5,2,7,3)
        for actual in range(TRANSFORMS):
            for candidate in range(TRANSFORMS):
                mapping=gauge_equivalent_mapping(actual,candidate,actual_mapping)
                self.assertEqual(len(set(mapping)),4)
                for action,slot in enumerate(mapping):
                    physical=actual_mapping.index(slot)
                    self.assertEqual(transformed_delta(candidate,action),transformed_delta(actual,physical))

    def test_gauge_average_is_normalized_and_keeps_nuisance_actions_zero(self):
        class Fixed:
            @staticmethod
            def probabilities(_):return [.1,.2,.3,.4]
        policy=object.__new__(GaugeAveragedPolicy);policy.field=Fixed();policy.sensor_mapping=tuple(range(6));policy.observed_channels=6
        policy.hypotheses=((0,(0,1,2,3)),(1,(2,3,1,0)));policy.observed_actions=5
        row=policy.probabilities(bytes(49*6))
        self.assertAlmostEqual(sum(row),1.);self.assertEqual(row[4],0.)
        for actual,expected in zip(row,[.25,.25,.2,.3,0.]):self.assertAlmostEqual(actual,expected)


if __name__=='__main__':unittest.main()
