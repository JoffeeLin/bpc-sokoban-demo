#!/usr/bin/env python3
import random,unittest

from bpc_cross_generator_v17 import (LabWorld,apply_slot,infer_bidirectional_support_binding,
    lab_raw,lab_step,nuisance_bit,same_cell_counts,same_cell_support_compatible,variable_expose)
from bpc_three_factor_v12 import World3,raw,step


class CrossGeneratorTest(unittest.TestCase):
    def test_independent_physics_matches_canonical_effects(self):
        rng=random.Random(17001)
        for _ in range(500):
            h,w=rng.choice((5,6,7)),rng.choice((5,6,7));border={y*w+x for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)}
            inside=[y*w+x for y in range(1,h-1) for x in range(1,w-1)];chosen=rng.sample(inside,5)
            old=World3(h,w,sum(1<<i for i in border),chosen[0],1<<chosen[1],1<<chosen[2],1<<chosen[3],1<<chosen[4])
            lab=LabWorld(*old.__dict__.values())
            self.assertEqual(lab_raw(lab),raw(old))
            for action in range(4):self.assertEqual(lab_step(lab,action).__dict__,step(old,action).__dict__)

    def test_nuisance_actuator_changes_only_extra_planes(self):
        world=LabWorld(5,5,0,6,0,0,0,0);sensors=(0,None,1,2,3,4,5,None);actions=(0,None,1,2,3)
        before=variable_expose(lab_raw(world),sensors,(3,4),0);nxt,phase=apply_slot(world,0,1,actions);after=variable_expose(lab_raw(nxt),sensors,(3,4),phase)
        self.assertEqual(world,nxt);self.assertNotEqual(before,after)
        for canonical,slot in enumerate((0,2,3,4,5,6)):self.assertEqual(before[slot::8],after[slot::8])

    def test_bidirectional_support_rejects_missing_reference_signature(self):
        class Stats:
            channels=2
        reference={frozenset(),frozenset((0,)),frozenset((1,))}
        target={frozenset(),frozenset((0,))}
        self.assertEqual(infer_bidirectional_support_binding(Stats(),reference,[(Stats(),target)])['compatible'],0)

    def test_same_cell_counts_ignore_action_value(self):
        before=bytes((1,0)*49);a=same_cell_counts([(before,0,before),(before,99,before)],2)
        self.assertEqual(a[(0,1)][0],{0:98});self.assertEqual(a[(0,1)][1],{})

    def test_conditional_support_requires_both_directions(self):
        reference={(0,1):({0:3,1:2},{0:4,1:1})};target={(0,1):({0:8,1:1},{0:2,1:9})}
        self.assertTrue(same_cell_support_compatible(reference,target,(0,1)))
        target[(0,1)][1].pop(1);self.assertFalse(same_cell_support_compatible(reference,target,(0,1)))


if __name__=='__main__':unittest.main()
