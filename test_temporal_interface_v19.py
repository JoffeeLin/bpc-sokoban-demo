#!/usr/bin/env python3
import random,unittest

from bpc_cross_generator_v17 import lab_world
from bpc_temporal_interface_v19 import scripted_observations


class TemporalInterfaceTest(unittest.TestCase):
    def test_sensor_and_actuator_delay_are_observationally_equivalent_at_fixed_sum(self):
        rng=random.Random(19001);world=lab_world(rng,'push');issued=tuple(rng.randrange(6) for _ in range(40))
        sensors=(0,1,2,3,4,5);actions=(0,1,2,3,None,None);kinds=()
        reference=scripted_observations(world,issued,sensors,actions,kinds,3,0,4)
        for sensor_delay in range(5):
            self.assertEqual(scripted_observations(world,issued,sensors,actions,kinds,3,sensor_delay,4-sensor_delay),reference)

    def test_different_total_lags_change_the_observation_trace(self):
        rng=random.Random(19002);world=lab_world(rng,'collect');issued=tuple(rng.randrange(4) for _ in range(80));sensors=(0,1,2,3,4,5);actions=(0,1,2,3)
        traces={scripted_observations(world,issued,sensors,actions,(),0,0,lag) for lag in range(5)}
        self.assertEqual(len(traces),5)


if __name__=='__main__':unittest.main()
