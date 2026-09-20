#!/usr/bin/env python3
"""Focused contracts for the v0.12 anonymous three-factor experiment."""
import unittest

from bpc_three_factor_v12 import FieldPolicy,ThreeFactorBPC,changed_planes,combined_candidate,key,raw,shortest,step


class StubCube:
    success_prior=[1,1,1,1]


class ThreeFactorTest(unittest.TestCase):
    def test_switch_clears_gate_and_exposes_raw_terminal_signature(self):
        rng=__import__('random').Random(12)
        while True:
            world=combined_candidate(rng)
            if shortest(world,'collect') is not None:break
        # Search a real trajectory to the first switch activation.
        frontier=[(world,[])];seen={key(world)}
        while frontier:
            state,path=frontier.pop(0)
            for action in range(4):
                nxt=step(state,action)
                if state.gates and not nxt.gates:
                    self.assertEqual(changed_planes(raw(state),raw(nxt)),(1,4,5));return
                identity=key(nxt)
                if identity not in seen:seen.add(identity);frontier.append((nxt,path+[action]))
        self.fail('switch was unreachable')

    def test_joint_world_needs_both_movable_objects_and_gates(self):
        world=combined_candidate(__import__('random').Random(13))
        self.assertIsNotNone(shortest(world,'collect'))
        self.assertIsNone(shortest(world,'collect',fixed_objects=True))
        self.assertIsNone(shortest(world,'collect',fixed_gates=True))

    def test_drop_indices_resolve_once_to_global_signatures(self):
        learner=ThreeFactorBPC();learner.factors={(1,2):StubCube(),(1,3):StubCube(),(1,4,5):StubCube()}
        policy=FieldPolicy(learner,drop=(1,))
        self.assertEqual(policy.drop,{(1,3)})
        state=bytes([0,1,1,0,1,1])
        self.assertEqual(tuple(x for x in learner.active(state) if x not in policy.drop),((1,2),(1,4,5)))


if __name__=='__main__':unittest.main()
