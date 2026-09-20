#!/usr/bin/env python3
"""Focused contracts for anonymous terminal co-change factor discovery."""
import unittest

from bpc_autofactor_v10 import AnonymousFactorBPC,changed_planes
from bpc_cross_task_v07 import World
from bpc_direct_composition_v09 import raw


class AutoFactorTest(unittest.TestCase):
    def test_changed_planes_have_no_entity_names(self):
        before=bytes((0,1,1,0, 0,0,0,1))
        after =bytes((0,0,0,0, 0,1,1,0))
        self.assertEqual(changed_planes(before,after),(1,2,3))

    def test_common_plane_is_removed_and_presence_routes(self):
        learner=AnonymousFactorBPC();learner.factors={(1,2):None,(1,3):None}
        self.assertEqual(learner.required_planes(),{(1,2):(2,),(1,3):(3,)})
        push=raw(World(5,5,32505887,12,1<<13,0))
        collect=raw(World(5,5,32505887,12,0,1<<13))
        both=raw(World(5,5,32505887,12,1<<13,1<<11))
        self.assertEqual(learner.active(push),((1,2),))
        self.assertEqual(learner.active(collect),((1,3),))
        self.assertEqual(learner.active(both),((1,2),(1,3)))


if __name__=='__main__':unittest.main()
