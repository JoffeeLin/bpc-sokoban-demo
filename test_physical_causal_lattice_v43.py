#!/usr/bin/env python3
import random,unittest

from physical_causal_lattice_v43 import CELLS,random_lattice,step_lattice


class CausalLatticeTest(unittest.TestCase):
    def test_generator_is_reproducible_and_has_fixed_boundary(self):
        a=random_lattice(random.Random(9),.1,.2,.6);b=random_lattice(random.Random(9),.1,.2,.6)
        self.assertEqual(a,b);self.assertEqual(len(a),CELLS);self.assertTrue(all(a[y*8+x]&1 for y in range(8) for x in range(8) if x in (0,7) or y in (0,7)))
    def test_terrain_is_persistent_and_causally_gates_motion(self):
        state=bytearray([0]*CELLS)
        for y in range(8):
            for x in range(8):
                if x in (0,7) or y in (0,7):state[y*8+x]=1
        state[3*8+3]=2;state[2*8+3]=4;state[3*8+4]=4
        blocked=step_lattice(bytes(state),0);moved=step_lattice(bytes(state),1)
        self.assertTrue(blocked[3*8+3]&2);self.assertFalse(moved[3*8+3]&2);self.assertTrue(moved[3*8+4]&2)
        self.assertEqual(bytes(v&5 for v in state),bytes(v&5 for v in moved))


if __name__=='__main__':unittest.main()
